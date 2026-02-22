set_languages("clatest", "cxxlatest")

add_rules "mode.debug"
add_rules "mode.release"

add_requires("nlohmann_json", "assimp")

local WX_ROOT = "D:/SDK/wx/3.3.1/"

target "SPETS"
    set_kind "binary" 
    
    add_packages("nlohmann_json", "assimp")

    if is_mode("debug") then 
        set_basename "SPETS_debug_$(arch)"    
        set_configdir "bin/dat"
    else
        set_basename "SPETS"
        set_configdir "package/bin/dat"
    end
        
    add_configfiles("dat/*", {onlycopy = true})

    set_targetdir "bin"
    set_objectdir "build/obj"
    
    add_includedirs "src/"
    add_headerfiles{ "src/**.h", "src/**.hpp" }

    add_defines("__WXMSW__", "WXUSINGDLL", "_UNICODE", "wxMSVC_VERSION_AUTO", "wxMSVC_VERSION_ABI_COMPAT", "NDEBUG")
    add_includedirs(WX_ROOT .. "include/", WX_ROOT .. "lib/", WX_ROOT .. "lib/vc14x_x64_dll/mswu/")
    add_linkdirs(WX_ROOT .. "lib/vc14x_x64_dll/")

    add_files(WX_ROOT .. "include/wx/msw/wx.rc")

    add_files{ "src/**.c", "src/**.cpp" }

target_end()
