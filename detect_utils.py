import cv2
import numpy as np
import torch
import torchvision
import torchvision.transforms as transforms
import torchvision.models as models

# Global variable to store the VGG model for saliency and face detection model
VGG_MODEL = models.vgg16(pretrained=True).eval()
FACE_MODEL = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=True).eval()

presets = [
    (1024, 1024), (1152, 896), (896, 1152), (1216, 832),
    (832, 1216), (1344, 768), (768, 1344), (1472, 704)
]

def compute_saliency_map(img):
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_tensor = transforms.ToTensor()(img_rgb).unsqueeze(0)

    # Hook the model to get gradient and output
    gradients = []
    def hook_function(module, grad_input, grad_output):
        # gradients.append(grad_input[0])
        gradients.append(grad_input[0].clone())

    first_layer = list(VGG_MODEL.features._modules.items())[0][1]
    first_layer.register_full_backward_hook(hook_function)

    # Forward pass
    img_tensor.requires_grad_()
    output = VGG_MODEL(img_tensor)
    
    # Take the maximum output value (predicted class)
    prediction_score, class_idx = torch.max(output, 1)
    prediction_score.backward()

    # Saliency map
    saliency = gradients[-1].squeeze().numpy()
    saliency = np.max(np.abs(saliency), axis=0)

    # Post-process saliency map
    saliency_blurred = cv2.GaussianBlur(saliency, (5, 5), 0)
    _, saliency_thresh = cv2.threshold(saliency_blurred, np.percentile(saliency_blurred, 95), 1, cv2.THRESH_BINARY)
    saliency_thresh = saliency_thresh.astype(np.uint8)

    # Calculate the centroid of the salient region
    moments = cv2.moments(saliency_thresh)
    centroid_x = int(moments["m10"] / moments["m00"])
    centroid_y = int(moments["m01"] / moments["m00"])
    
    # Return a bounding box around the centroid
    box_size = 100
    return (centroid_x - box_size//2, centroid_y - box_size//2, box_size, box_size)

def detect_face_torch(img):
    transform = torchvision.transforms.Compose([torchvision.transforms.ToTensor()])
    img_tensor = transform(img).unsqueeze(0)

    with torch.no_grad():
        prediction = FACE_MODEL(img_tensor)

    if len(prediction[0]['labels']) == 0:
        return None
    else:
        box = prediction[0]['boxes'][0].cpu().numpy()
        return [int(coord) for coord in box]  # Convert coordinates to integers

def best_crop(image_path, presets):
    img = cv2.imread(image_path)
    
    box = detect_face_torch(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))  # Convert to RGB before passing to the model

    if box is None:
        print(f"No face detected in {image_path}. Using saliency map to identify region of interest.")
        box = compute_saliency_map(img)
        if box is None:
            print(f"Failed to compute saliency map for {image_path}. Using original image.")
            return img, (img.shape[1], img.shape[0])  # Return original image and its dimensions

    fx, fy, fw, fh = box[0], box[1], box[2], box[3]
    padding_factor = dynamic_padding(img, fw, fh)

    # Create a padded bounding box around the detected area
    left = max(0, fx - int(padding_factor * fw) // 2)
    right = min(img.shape[1], fx + fw + int(padding_factor * fw) // 2)
    top = max(0, fy - int(padding_factor * fh) // 2)
    bottom = min(img.shape[0], fy + fh + int(padding_factor * fh) // 2)

    # Adjust the bounding box to match the closest preset ratio
    current_aspect_ratio = (right - left) / (bottom - top)
    is_portrait = img.shape[0] > img.shape[1]
    valid_presets = [p for p in presets if (p[1] >= p[0] if is_portrait else p[0] >= p[1])]
    
    # Find the closest preset aspect ratio
    preset_ratios = [w/h for w, h in valid_presets]
    closest_preset_index = min(range(len(preset_ratios)), key=lambda i: abs(preset_ratios[i] - current_aspect_ratio))
    target_w, target_h = valid_presets[closest_preset_index]

    target_ratio = target_w / target_h
    center_x, center_y = (left + right) // 2, (top + bottom) // 2

    if current_aspect_ratio > target_ratio:
        # Adjust width to match target_ratio
        new_width = target_ratio * (bottom - top)
        left = center_x - new_width // 2
        right = center_x + new_width // 2
    else:
        # Adjust height to match target_ratio
        new_height = (right - left) / target_ratio
        top = center_y - new_height // 2
        bottom = center_y + new_height // 2

    # Clip values to ensure they remain within image boundaries
    left, right = max(0, left), min(img.shape[1], right)
    top, bottom = max(0, top), min(img.shape[0], bottom)

    cropped_img = img[int(top):int(bottom), int(left):int(right)]

    # Resize the cropped image to the target preset size
    final_cropped_img = cv2.resize(cropped_img, (target_w, target_h), interpolation=cv2.INTER_AREA)

    return final_cropped_img, (target_w, target_h)

def dynamic_padding(img, fw, fh):
    height, width, _ = img.shape
    face_proportion_width = fw / width
    face_proportion_height = fh / height

    if face_proportion_width > 0.6 or face_proportion_height > 0.6:
        return 1.1
    elif face_proportion_width < 0.2 or face_proportion_height < 0.2:
        return 2.5
    else:
        return 1.5