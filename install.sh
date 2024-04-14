sudo apt install -y ros-humble-gazebo-*
sudo apt install -y ros-humble-xacro
sudo apt install -y ros-humble-robot-state-publisher
sudo apt install -y ros-humble-joint-state-publisher
sudo apt install -y ros-humble-rviz2
sudo apt install -y ros-humble-nav2*
sudo apt install -y ros-humble-slam-toolbox
sudo apt install -y ros-humble-pcl-ros
sudo apt install -y ros-humble-pcl-conversions
sudo apt install -y ros-humble-libpointmatcher
sudo apt install -y ros-humble-tf2-geometry-msgs
sudo apt install -y libboost-all-dev
sudo apt install -y libgoogle-glog-dev
sudo apt install -y ros-humble-serial-driver
sudo apt install -y ros-humble-rmw-cyclonedds-cpp

export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
source /usr/share/gazebo/setup.sh