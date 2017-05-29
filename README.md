# SimpleBmpResolver
## a simple bmp format picture processing tool
## function
1. resolver a bmp file
2. resize
3. graying
4. rotate
## use
```python
bmp = Bmp() #create a new bmp
# start resolver
bmp.parse('filename') #resovler a new bmp file must have
# start operation
bmp.rotate()  # rotate
bmp.resize(width, height)  #resize
bmp.graying()  # graying
bmp.generate('target_file_path') #use this to save change
```
## problems
1. don't have error checking
2. rotation only can rotate anticlockwise 90°
3. unknown errors (-.-)
***
## 简单的BMP图像处理工具
本人英语比较渣。。这里说声抱歉。
入门者可以查看该源码来获得一些基本的图像处理思路（因为我也是小白~）
## 功能
1. 解析BMP文件
2. 放大、缩小
3. 灰度化
4. 旋转
## 问题
1. 没有错误检查
2. 只能逆时针旋转90°
3. 未知错误若干 （手动滑稽）
