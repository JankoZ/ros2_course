cmake_minimum_required(VERSION 3.8)
project(gazebo_controller_pkg)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

ament_python_install_package(${PROJECT_NAME})

install(PROGRAMS
  gazebo_controller_pkg/wall_follower.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
