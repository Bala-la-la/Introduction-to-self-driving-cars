#!/usr/bin/env python3

"""
2D Controller Class to be used for the CARLA waypoint follower demo.
"""

import cutils
import numpy as np


class Controller2D(object):
    def __init__(self, waypoints):
        self.vars = cutils.CUtils()
        self._current_x = 0
        self._current_y = 0
        self._current_yaw = 0
        self._current_speed = 0
        self._desired_speed = 0
        self._current_frame = 0
        self._current_timestamp = 0
        self._start_control_loop = False
        self._set_throttle = 0
        self._set_brake = 0
        self._set_steer = 0
        self._waypoints = waypoints
        self._conv_rad_to_steer = 180.0 / 70.0 / np.pi
        self._pi = np.pi
        self._2pi = 2.0 * np.pi

    def update_values(self, x, y, yaw, speed, timestamp, frame):
        self._current_x = x
        self._current_y = y
        self._current_yaw = yaw
        self._current_speed = speed
        self._current_timestamp = timestamp
        self._current_frame = frame
        if self._current_frame:
            self._start_control_loop = True

    def update_desired_speed(self):
        min_idx = 0
        min_dist = float("inf")
        desired_speed = 0
        for i in range(len(self._waypoints)):
            dist = np.linalg.norm(np.array([
                self._waypoints[i][0] - self._current_x,
                self._waypoints[i][1] - self._current_y]))
            if dist < min_dist:
                min_dist = dist
                min_idx = i
        if min_idx < len(self._waypoints) - 1:
            desired_speed = self._waypoints[min_idx][2]
        else:
            desired_speed = self._waypoints[-1][2]
        self._desired_speed = desired_speed

    def update_waypoints(self, new_waypoints):
        self._waypoints = new_waypoints

    def get_commands(self):
        return self._set_throttle, self._set_steer, self._set_brake

    def set_throttle(self, input_throttle):
        # Clamp the throttle command to valid bounds
        throttle = np.fmax(np.fmin(input_throttle, 1.0), 0.0)
        self._set_throttle = throttle

    def set_steer(self, input_steer_in_rad):
        # Covnert radians to [-1, 1]
        input_steer = self._conv_rad_to_steer * input_steer_in_rad

        # Clamp the steering command to valid bounds
        steer = np.fmax(np.fmin(input_steer, 1.0), -1.0)
        self._set_steer = steer

    def set_brake(self, input_brake):
        # Clamp the steering command to valid bounds
        brake = np.fmax(np.fmin(input_brake, 1.0), 0.0)
        self._set_brake = brake

    def update_controls(self):
        ######################################################
        # RETRIEVE SIMULATOR FEEDBACK
        ######################################################
        x = self._current_x
        y = self._current_y
        yaw = self._current_yaw
        v = self._current_speed
        self.update_desired_speed()
        v_desired = self._desired_speed
        t = self._current_timestamp
        waypoints = self._waypoints
        throttle_output = 0
        steer_output = 0
        brake_output = 0

        ######################################################
        ######################################################
        # MODULE 7: DECLARE USAGE VARIABLES HERE
        ######################################################
        ######################################################
        """
            Use 'self.vars.create_var(<variable name>, <default value>)'
            to create a persistent variable (not destroyed at each iteration).
            This means that the value can be stored for use in the next
            iteration of the control loop.

            Example: Creation of 'v_previous', default value to be 0
            self.vars.create_var('v_previous', 0.0)

            Example: Setting 'v_previous' to be 1.0
            self.vars.v_previous = 1.0

            Example: Accessing the value from 'v_previous' to be used
            throttle_output = 0.5 * self.vars.v_previous
        """
        self.vars.create_var('v_previous', 0.0)
        self.vars.create_var('e_previous', 0.0)
        self.vars.create_var('e_total', 0.0)
        self.vars.create_var('steer_output_p', 0.0)

        # Skip the first frame to store previous values properly
        if self._start_control_loop:
            """
                Controller iteration code block.

                Controller Feedback Variables:
                    x               : Current X position (meters)
                    y               : Current Y position (meters)
                    yaw             : Current yaw pose (radians)
                    v               : Current forward speed (meters per second)
                    t               : Current time (seconds)
                    v_desired       : Current desired speed (meters per second)
                                      (Computed as the speed to track at the
                                      closest waypoint to the vehicle.)
                    waypoints       : Current waypoints to track
                                      (Includes speed to track at each x,y
                                      location.)
                                      Format: [[x0, y0, v0],
                                               [x1, y1, v1],
                                               ...
                                               [xn, yn, vn]]
                                      Example:
                                          waypoints[2][1]: 
                                          Returns the 3rd waypoint's y position

                                          waypoints[5]:
                                          Returns [x5, y5, v5] (6th waypoint)

                Controller Output Variables:
                    throttle_output : Throttle output (0 to 1)
                    steer_output    : Steer output (-1.22 rad to 1.22 rad)
                    brake_output    : Brake output (0 to 1)
            """

            ######################################################
            ######################################################
            # MODULE 7: IMPLEMENTATION OF LONGITUDINAL CONTROLLER HERE
            ######################################################
            ######################################################
            """
                Implement a longitudinal controller here. Remember that you can
                access the persistent variables declared above here. For
                example, can treat self.vars.v_previous like a "global variable".
            """

            # Change these outputs with the longitudinal controller. Note that
            # brake_output is optional and is not required to pass the
            # assignment, as the car will naturally slow down over time.
            K_p = 0.2
            K_d = 0.05
            K_i = 0.01

            error_v = self._desired_speed - self._current_speed
            self.vars.e_total += error_v
            target_acc = K_p * (error_v) + K_i * self.vars.e_total + K_d * (error_v - self.vars.e_previous)

            if (target_acc < 0):
                brake_output = np.absolute(target_acc)
            else:
                throttle_output = target_acc

            self.vars.e_previous = error_v
            ######################################################
            ######################################################
            # MODULE 7: IMPLEMENTATION OF LATERAL CONTROLLER HERE
            ######################################################
            ######################################################
            """
                Implement a lateral controller here. Remember that you can
                access the persistent variables declared above here. For
                example, can treat self.vars.v_previous like a "global variable".
            """

            # Change the steer output with the lateral controller.

            idx = len(self._waypoints) - 1
            dist = 10000000
            laterr = 0
            idy = 0

            # Find the nearest waypoint
            for i in range(len(self._waypoints)):
                dist1 = np.sqrt(
                    (self._waypoints[i][0] - self._current_x) ** 2 + (self._waypoints[i][1] - self._current_y) ** 2)
                if dist1 < dist:
                    dist = dist1
                    idx = i

            if idx < len(self._waypoints) - 18:
                idy = idx + 17
            else:
                idy = len(self._waypoints) - 1
            #取得是点到平行线的距离作为横向误差
            alpha = np.arctan2(waypoints[idy][1] - waypoints[idx][1], waypoints[idy][0] - waypoints[idx][0])
            laterr = (self._current_x - waypoints[idx][0]) * np.sin(alpha) + (
                        self._current_y - waypoints[idx][1]) * np.cos(alpha)

            yaw_path = np.arctan2(waypoints[idy][1] - waypoints[idx][1], waypoints[idy][0] - waypoints[idx][0])

            theta_fai = yaw_path - yaw

            if theta_fai > np.pi:
                theta_fai = theta_fai - 2 * np.pi
            elif theta_fai < -np.pi:
                theta_fai = theta_fai + 2 * np.pi
            else:
                theta_fai = theta_fai

            crosstrack_error = laterr
            yaw_cross_track = np.arctan2(y - waypoints[0][1], x - waypoints[0][0])
            #yaw_path2ct = np.arctan2(waypoints[-1][1] - waypoints[0][1],
            #                         waypoints[-1][0] - waypoints[0][0]) - yaw_cross_track
            yaw_path2ct = yaw_path - yaw_cross_track
            if yaw_path2ct > np.pi:
                yaw_path2ct -= 2 * np.pi
            if yaw_path2ct < - np.pi:
                yaw_path2ct += 2 * np.pi
            if theta_fai > 0:
                crosstrack_error = abs(crosstrack_error)
            else:
                crosstrack_error = - abs(crosstrack_error)
            yaw_diff_crosstrack = np.arctan(5 * crosstrack_error / (v))

            # final expected steering
            steer_expect = yaw_diff_crosstrack + theta_fai
            if steer_expect > np.pi:
                steer_expect -= 2 * np.pi
            if steer_expect < - np.pi:
                steer_expect += 2 * np.pi
            steer_expect = min(1.22, steer_expect)
            steer_expect = max(-1.22, steer_expect)
            #000

            # update
            steer_output = steer_expect

            # Set steering angle
            # steer_output = theta_fai + theta_y
            s1 = steer_output

            ######################################################
            # SET CONTROLS OUTPUT
            ######################################################
            self.set_throttle(throttle_output)  # in percent (0 to 1)
            self.set_steer(steer_output)  # in rad (-1.22 to 1.22)
            self.set_brake(brake_output)  # in percent (0 to 1)
            #参考自https://github.com/ritz441/Self-driving-car/blob/main/controller2d.py
            #另外采用stanley控制的 https://github.com/Mostafa-wael/Self-Driving-Vehicle-Control-on-CARLA/blob/master/controller2d.py
            #mpc控制的https://github.com/sapan-ostic/Carla-Controllers/blob/main/Course1FinalProject/controller2d.py
            #采用纯跟踪https://github.com/ahmedmoawad124/Self-Driving-Vehicle-Control/blob/master/controller2d.py
            #全面的大佬https://github.com/munirjojoverge/Self-Driving-Vehicle-Control-Using-Carla

        ######################################################
        ######################################################
        # MODULE 7: STORE OLD VALUES HERE (ADD MORE IF NECESSARY)
        ######################################################
        ######################################################
        """
            Use this block to store old values (for example, we can store the
            current x, y, and yaw values here using persistent variables for use
            in the next iteration)
        """
        self.vars.v_previous = v
        self.vars.steer_output_p = s1  # Store forward speed to be used in next step