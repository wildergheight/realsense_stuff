## License: Apache 2.0. See LICENSE file in root directory.
## Copyright(c) 2017 Intel Corporation. All Rights Reserved.

#####################################################
##              Align Depth to Color               ##
#####################################################

# First import the library
import pyrealsense2 as rs
# Import Numpy for easy array manipulation
import numpy as np
# Import OpenCV for easy image rendering
import cv2

x_coord = 50
y_coord = 50


def click_event(event, x, y, flags, params):
    global x_coord
    global y_coord
    # checking for left mouse clicks
    if event == cv2.EVENT_LBUTTONDOWN:
        # displaying the coordinates
        # on the Shell
        # print(x, ' ', y)
        x_coord = y
        y_coord = x


# Create a pipeline


pipeline = rs.pipeline()

# Create a config and configure the pipeline to stream
#  different resolutions of color and depth streams
config = rs.config()

# Get device product line for setting a supporting resolution
pipeline_wrapper = rs.pipeline_wrapper(pipeline)
pipeline_profile = config.resolve(pipeline_wrapper)
device = pipeline_profile.get_device()
device_product_line = str(device.get_info(rs.camera_info.product_line))

found_rgb = False
for s in device.sensors:
    if s.get_info(rs.camera_info.name) == 'RGB Camera':
        found_rgb = True
        break
if not found_rgb:
    print("The demo requires Depth camera with Color sensor")
    exit(0)

# config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)


if device_product_line == 'L500':
    config.enable_stream(rs.stream.color, 960, 540, rs.format.bgr8, 30)
else:
    # config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)

# Start streaming
profile = pipeline.start(config)

# Getting the depth sensor's depth scale (see rs-align example for explanation)
depth_sensor = profile.get_device().first_depth_sensor()
depth_scale = depth_sensor.get_depth_scale()
print("Depth Scale is: ", depth_scale)

# We will be removing the background of objects more than
#  clipping_distance_in_meters meters away
clipping_distance_in_meters = 10  # 1 meter
clipping_distance = clipping_distance_in_meters / depth_scale

# Create an align object
# rs.align allows us to perform alignment of depth frames to others frames
# The "align_to" is the stream type to which we plan to align depth frames.
align_to = rs.stream.color
align = rs.align(align_to)

# Streaming loop
try:
    while True:
        # Get frameset of color and depth
        frames = pipeline.wait_for_frames()
        # frames.get_depth_frame() is a 640x360 depth image

        # Align the depth frame to color frame
        aligned_frames = align.process(frames)

        # Get aligned frames
        aligned_depth_frame = aligned_frames.get_depth_frame()  # aligned_depth_frame is a 640x480 depth image
        color_frame = aligned_frames.get_color_frame()

        # Validate that both frames are valid
        if not aligned_depth_frame or not color_frame:
            continue

        depth_image = np.asanyarray(aligned_depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())
        # rgb_value_center = color_image[y_coord, x_coord]
        rgb_value_center = color_image[x_coord, y_coord]

        print(rgb_value_center)

        # Create a circular mask
        mask = np.zeros_like(color_image)
        # cv2.circle(mask, (x_coord, y_coord), 10, (255, 255, 255), thickness=cv2.FILLED)
        start_point_x = x_coord - 5
        if start_point_x < 0:
            start_point_x = 0
        start_point_y = y_coord - 5
        if start_point_y < 0:
            start_point_y = 0
        end_point_x = x_coord + 5
        if end_point_x > 480:
            end_point_x = 480
        end_point_y = y_coord + 5
        if end_point_y > 640:
            end_point_y = 640
        cv2.rectangle(mask, (start_point_y, start_point_x), (end_point_y, end_point_x), (255, 255, 255),
                      thickness=cv2.FILLED)
        # Apply the mask to the image data to extract the circular region
        result = cv2.bitwise_and(color_image, mask)

        # If you want to get the average color in the circle
        new_arr = result[start_point_x:end_point_x+1,start_point_y:end_point_y+1]
        average_color = np.mean(new_arr, axis=(0, 1))
        print(average_color)

        images = color_image

        cv2.namedWindow('Align Example', cv2.WINDOW_NORMAL)

        # Center coordinates
        center_coordinates = (y_coord, x_coord)

        # Radius of circle
        radius = 10

        # Blue color in BGR
        color = (255, 0, 0)

        # Line thickness of 2 px
        thickness = 2

        # Using cv2.circle() method
        # Draw a circle with blue line borders of thickness of 2 px
        image = cv2.circle(images, center_coordinates, radius, color, thickness)

        cv2.imshow('Align Example', images)

        cv2.setMouseCallback('Align Example', click_event)

        key = cv2.waitKey(1)

        # Press esc or 'q' to close the image window
        if key & 0xFF == ord('q') or key == 27:
            cv2.destroyAllWindows()
            break
finally:
    pipeline.stop()
