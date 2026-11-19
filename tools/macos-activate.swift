// Make an installed keyboard layout bundle available without logging out,
// and enable the layout so it shows up in the input menu.
//
// A layout that macOS already lists isn't registered again: every
// registration adds another entry to this session's input sources, and it
// doesn't make macOS load a replaced bundle anyway (that takes logging out).
//
// Usage: swift tools/macos-activate.swift BUNDLE
//
// The input sources are looked up by the bundle's identifier, since macOS
// may derive their IDs differently from what Info.plist declares.

import Carbon
import Foundation

let args = CommandLine.arguments
guard args.count == 2 else {
    FileHandle.standardError.write("Usage: macos-activate.swift BUNDLE\n".data(using: .utf8)!)
    exit(2)
}
let url = URL(fileURLWithPath: args[1])
guard let bundleID = Bundle(url: url)?.bundleIdentifier else {
    print("\(args[1]) isn't a bundle with an identifier.")
    exit(1)
}
let bundle = url as CFURL

func property<T>(_ source: TISInputSource, _ key: CFString) -> T {
    Unmanaged<AnyObject>.fromOpaque(TISGetInputSourceProperty(source, key)).takeUnretainedValue() as! T
}

let filter = [kTISPropertyBundleID as String: bundleID] as CFDictionary
func installedSources() -> [TISInputSource] {
    TISCreateInputSourceList(filter, true)?.takeRetainedValue() as? [TISInputSource] ?? []
}

var sources = installedSources()
if sources.isEmpty {
    let status = TISRegisterInputSource(bundle)
    if status != noErr {
        print("Registering \(args[1]) failed (OSStatus \(status)); log out and back in instead.")
        exit(1)
    }
    sources = installedSources()
}
guard let source = sources.first else {
    print("Registered \(args[1]), but macOS doesn't list it yet; log out and back in instead.")
    exit(1)
}
let name: String = property(source, kTISPropertyLocalizedName)
let enabled = TISEnableInputSource(source)
if enabled != noErr {
    print("Couldn't enable \(name) (OSStatus \(enabled)); add it in System Settings instead.")
    exit(1)
}
// macOS can report success without changing anything, e.g., when this
// session's input source list is stale after reinstalls; check the result.
let fresh = installedSources()
let isEnabled = fresh.contains { (property($0, kTISPropertyInputSourceIsEnabled) as CFBoolean) == kCFBooleanTrue }
if !isEnabled {
    print("macOS didn't enable \"\(name)\" in this session; log out and back in, then add it in System Settings.")
    exit(1)
}
print("Enabled \"\(name)\"; select it in the input menu.")
