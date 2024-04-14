sudo chmod 777 /dev/ttyS0
source install/setup.sh
ros2 launch rm_nav_bringup bringup_sim.launch.py world:=RMUC mode:=mapping
