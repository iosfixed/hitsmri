import torch
from torch import nn
import torch.nn.functional as F

class DoubleConv(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.c1 = nn.Conv2d(in_ch, out_ch, 3)
        self.c2 = nn.Conv2d(out_ch, out_ch, 3)

        self.bn1 = nn.BatchNorm2d(out_ch)
        self.bn2 = nn.BatchNorm2d(out_ch)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.c1(x)
        x = self.relu(x)

        x = self.bn1(x)

        x = self.c2(x)
        x = self.relu(x)

        x = self.bn2(x)
        return x


class UNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.c1 = DoubleConv(3, 64)
        self.c2 = DoubleConv(64, 128)
        self.c3 = DoubleConv(128, 256)
        self.c4 = DoubleConv(256, 512)
        self.c5 = DoubleConv(512, 512)

        self.c6 = DoubleConv(1024, 256)
        self.c7 = DoubleConv(512, 128)
        self.c8 = DoubleConv(256, 64)
        self.c9 = DoubleConv(128, 64)
        self.c10 = nn.Conv2d(64, 1, kernel_size=1)

        self.pool = nn.MaxPool2d(2)
        self.up = nn.Upsample(scale_factor=2)
        self.out_up = nn.Upsample((256, 256))
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.c1(x)
        x1 = x.clone()

        x = self.pool(x)
        x = self.c2(x)
        x2 = x.clone()

        x = self.pool(x)
        x = self.c3(x)
        x3 = x.clone()

        x = self.pool(x)
        x = self.c4(x)
        x4 = x.clone()

        x = self.pool(x)
        x = self.c5(x)

        x = self.up(x)
        x = resize_and_cat(x4, x)
        x = self.c6(x)

        x = self.up(x)
        x = resize_and_cat(x3, x)
        x = self.c7(x)

        x = self.up(x)
        x = resize_and_cat(x2, x)
        x = self.c8(x)

        x = self.up(x)
        x = resize_and_cat(x1, x)
        x = self.c9(x)

        x = self.c10(x)
        x = self.out_up(x)
        x = self.sigmoid(x)

        return x


def resize_and_cat(x1, x2):
    # x1 - это остатки с левой части, имеет больший размер
    # x2 - соответственно, результаты правой

    # можем попробовать upsample вместо паддинга
    dx = x1.size(2) - x2.size(2)
    dy = x1.size(3) - x2.size(3)

    xpad = (dx // 2, dx - dx // 2)
    ypad = (dy // 2, dy - dy // 2)

    x2 = F.pad(x2, (*ypad, *xpad))

    return torch.cat([x1, x2], dim=1)

if __name__ == '__main__':
    tensor = torch.rand(1, 3, 256, 256)
    net = UNet()
    net(tensor)