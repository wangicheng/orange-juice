from typing import Union
import io
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image
from django.conf import settings

CHAR_SET = "abcdefghkmnpqrstuvwxyzABCDEFGHGKMNOPQRSTUVWXYZ23456789"
INT_TO_CHAR = {i: char for i, char in enumerate(CHAR_SET)}
NUM_CHARS = len(CHAR_SET)

class CaptchaCNN(nn.Module):
    def __init__(self, num_chars=NUM_CHARS, num_digits=4):
        super(CaptchaCNN, self).__init__()
        self.num_chars = num_chars
        self.num_digits = num_digits

        # 定義卷積層
        self.conv1 = nn.Conv2d(1, 32, 3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.pool1 = nn.MaxPool2d(2, 2)

        self.conv2 = nn.Conv2d(32, 64, 3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.pool2 = nn.MaxPool2d(2, 2)

        self.conv3 = nn.Conv2d(64, 128, 3, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.pool3 = nn.MaxPool2d(2, 2)

        self.conv4 = nn.Conv2d(128, 256, 3, padding=1)
        self.bn4 = nn.BatchNorm2d(256)
        self.pool4 = nn.MaxPool2d(2, 2)

        self.flattened_features = 256 * 1 * 5
        self.fc_shared = nn.Linear(self.flattened_features, 512)

        self.fc_digit1 = nn.Linear(512, self.num_chars)
        self.fc_digit2 = nn.Linear(512, self.num_chars)
        self.fc_digit3 = nn.Linear(512, self.num_chars)
        self.fc_digit4 = nn.Linear(512, self.num_chars)

    def forward(self, x):
        # 卷積層
        x = self.pool1(F.relu(self.bn1(self.conv1(x))))
        x = self.pool2(F.relu(self.bn2(self.conv2(x))))
        x = self.pool3(F.relu(self.bn3(self.conv3(x))))
        x = self.pool4(F.relu(self.bn4(self.conv4(x))))

        # 展平
        x = x.view(x.size(0), -1) # x.size(0) 是 batch_size

        # 共享全連接層
        x = F.relu(self.fc_shared(x))

        # 每個分類頭獨立預測
        output1 = self.fc_digit1(x)
        output2 = self.fc_digit2(x)
        output3 = self.fc_digit3(x)
        output4 = self.fc_digit4(x)

        return output1, output2, output3, output4

class CaptchaPredictor:
    def __init__(self, model_path):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = CaptchaCNN().to(self.device)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()
        
        self.transform = transforms.Compose([
            transforms.Grayscale(num_output_channels=1),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5], std=[0.5])
        ])

    def predict(self, image: Union[Image.Image, str, io.BytesIO]):
        if not isinstance(image, Image.Image):
            image = Image.open(image).convert('RGB')
        
        image = self.transform(image).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(image)
            predicted = [torch.argmax(output, dim=1).item() for output in outputs]
            result = ''.join(INT_TO_CHAR[idx] for idx in predicted)
            
        return result


predictor_instance: CaptchaPredictor = None

def solve_captcha(image_data: Union[str, io.BytesIO]) -> str:
    """
    使用常駐記憶體的模型來辨識驗證碼。
    
    Args:
        image_data: 圖片的檔案路徑或 bytes 數據。

    Returns:
        辨識出的字串。
    """
    global predictor_instance
    if predictor_instance is None:
        predictor_instance = CaptchaPredictor(model_path=settings.CNN_MODEL_PATH)
        
    return predictor_instance.predict(image_data)