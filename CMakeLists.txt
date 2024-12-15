cmake_minimum_required(VERSION 3.25)
project(DB)

set(CMAKE_CXX_STANDARD 23)
include(FetchContent)

FetchContent_Declare(json URL https://github.com/nlohmann/json/releases/download/v3.11.3/json.tar.xz)
FetchContent_MakeAvailable(json)

add_executable(DB
        DB/server.cpp
        DB/makeStructure.cpp
        DB/insert.cpp
        DB/common.cpp
        DB/delete.cpp
        DB/select.cpp
        DB/userQuery.cpp
        classes/arr.cpp
        )


target_link_libraries(DB PRIVATE nlohmann_json::nlohmann_json)
