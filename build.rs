fn main() {
    // All Slint UI compiled through one unified entry point
    // This ensures all types (structs + components) are available in one include_modules!()
    let entry = "ui/cm.slint";
    println!("cargo:rerun-if-changed={}", entry);

    // Watch all sub-files too
    let sub_files = [
        "ui/environment/main.slint",
        "ui/environment/settings.slint",
        "ui/environment/about.slint",
        "ui/environment/calculator.slint",
        "ui/environment/container_manager.slint",
        "ui/environment/emoji_picker.slint",
        "ui/environment/clipboard_manager.slint",
        "ui/environment/lockscreen.slint",
        "ui/mode/main.slint",
        "ui/please/main.slint",
    ];
    for f in &sub_files {
        println!("cargo:rerun-if-changed={}", f);
    }

    println!("cargo:rerun-if-changed=source-code/");

    if std::path::Path::new(entry).exists() {
        if let Err(e) = slint_build::compile(entry) {
            panic!("Slint compile error in {}: {}", entry, e);
        }
    } else {
        eprintln!("cargo:warning=Slint entry point not found: {}", entry);
    }
}
