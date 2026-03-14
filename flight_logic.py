import numpy as np
# from djitellopy import tello

max_speed_saturation = 100
area_range = [25000,55000]
# drone = tello.Tello()

# Notes For PID Control
# left_right_velocity: LEFT=-100 & RIGHT=100
# forward_backward_velocity: FORWARD=-100 & BACKWARD=100
# up_down_velocity: UP=-100 & DOWN=100
# yaw_velocity:	LEFT=-100 & RIGHT=100
    
class PID():
    def __init__(self,Kpy,Kiy,Kdy,Kpyaw,Kiyaw,Kdyaw):
        # self.Kpx = Kpx
        # self.Kix = Kix
        # self.Kdx = Kdx
        self.Kpy = Kpy
        self.Kiy = Kiy
        self.Kdy = Kdy
        self.Kpyaw = Kpyaw
        self.Kiyaw = Kiyaw
        self.Kdyaw = Kdyaw
        # self.error_x = 0
        self.error_y = 0
        self.error_yaw = 0
        # self.previous_error_x = 0
        self.previous_error_y = 0
        self.previous_error_yaw = 0
        # self.integral_error_x = 0
        self.integral_error_y = 0
        self.integral_error_yaw = 0
        # self.derivative_error_x = 0
        self.derivative_error_y = 0
        self.derivative_error_yaw = 0
        # self.output_x = 0
        self.output_y = 0
        self.output_yaw = 0

    def computation(self,center_x,center_y,width,height,bbox_area_1):

        # previous_time = time.time()-0.001

        # diff_time = abs(current_time - previous_time)
        # diff_time = 0.1

        # if center_x == 0:
        #     # self.error_x = 0
        #     # self.output_x = 0
        #     self.output_yaw = 0

        if bbox_area_1 > int(area_range[0]) and bbox_area_1 < int(area_range[1]):
            forward_backward_velocity = 0
        elif bbox_area_1 > int(area_range[1]):
            forward_backward_velocity = -35
        elif bbox_area_1 < int(area_range[0]) and bbox_area_1 != 0:
            forward_backward_velocity = 35
        
        # if center_y == 0:
        #     self.error_y = 0
        #     self.output_y = 0
        #     self.output_yaw = 0
        # else:
            # self.error_x = center_x - #Change
        self.error_y = center_y - height
        self.error_yaw = center_x - width
            
            # self.integral_error_x += self.error_x * diff_time
        self.integral_error_y += self.error_y
        self.integral_error_yaw += self.error_yaw 

            # self.derivative_error_x = self.error_x - self.previous_error_x / diff_time
        self.derivative_error_y = self.error_y - self.previous_error_y
        self.derivative_error_yaw = self.error_yaw - self.previous_error_yaw 

            # PID Formula: u(t) = Kpe(t) [Proportional] + Ki∫te(τ)dτ [Integral] + Kde˙(t) [Derivative]
            # self.output_x = self.Kpx * self.error_x + self.Kix * self.integral_error_x + self.Kdx * self.derivative_error_x
        self.output_y = self.Kpy * self.error_y + self.Kiy * self.integral_error_y + self.Kdy * self.derivative_error_y
        self.output_yaw = self.Kpyaw * self.error_yaw + self.Kiyaw * self.integral_error_yaw + self.Kdyaw * self.derivative_error_yaw

        self.output_yaw = np.clip(self.output_yaw,-100,100)
        self.output_y = np.clip(self.output_yaw,-100,100)

            # self.previous_error_x = self.error_x
        self.previous_error_y = self.error_y
        self.previous_error_yaw = self.error_yaw
            # previous_time = current_time

        # max_speed_saturation global paramater of 100
                
                # print(f"Output_X: {int(self.output_x)}") # 100
                # print(f"Forward_Backward_Velocity: {int(forward_backward_velocity)}") # -20
                # print(f"Output_Y: {int(self.output_y)}") # 100
                # print(f"Output_YAW: {int(self.output_yaw)}")
                
                # int(forward_backward_velocity): PASSED
                # int(self.output_x): FAILED
                # int(self.output_y): FAILED
                # int(self.output_yaw): PASSED

        # drone.send_rc_control(0, int(forward_backward_velocity), int(self.output_y), int(self.output_yaw))
        # print(f"Output_X: {int(self.output_x)}")
        print(f"Forward_Backward_Velocity: {int(forward_backward_velocity)}")
        print(f"Output_Y: {int(self.output_y)}")
        print(f"Output_YAW: {int(self.output_yaw)}")
