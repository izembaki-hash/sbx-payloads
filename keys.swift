//
//  MobileGestaltKeys.swift
//  mobilegestaltparser
//

import Foundation


struct MobileGestaltKey: Identifiable {
    let id = UUID()
    let realKey: String
    let obfuscatedKey: String
    let offset: Int64
    let value: UInt64
    let hasOffset: Bool
    
    var hexValue: String {
        String(format: "0x%llx", value)
    }
    
    var byteRepresentation: String {
        var bytes = [UInt8]()
        for i in 0..<8 {
            bytes.append(UInt8((value >> (i * 8)) & 0xFF))
        }
        return bytes.map { String(format: "%02x", $0) }.joined(separator: " ")
    }
    
    static func load() -> [MobileGestaltKey] {
        
    
        let modifier = PlistModifier()
        
        var output:[MobileGestaltKey] = []
        
        DispatchQueue.global(priority: .background).async {
            
            modifier.makeRequest(withFirefoxUserAgent: "file://private/var/containers/Shared/SystemGroup/systemgroup.com.apple.mobilegestaltcache/Library/Caches/com.apple.MobileGestalt.plist") { (dictionary, error) in
                DispatchQueue.main.async {
                    if let error = error {
                        print("Error: \(error.localizedDescription)")
                        return
                    }
                    
                    if let dict = dictionary as? [String: Any] {
                        if let result = modifier.loadPlist(withReturn: dict) as? [[String: Any]] {
                            print("Got result: \(result)")
                            output = result.map { dict in
                                MobileGestaltKey(
                                    realKey: dict["realKey"] as? String ?? "unknown",
                                    obfuscatedKey: dict["obfuscatedKey"] as? String ?? "",
                                    offset: (dict["offset"] as? NSNumber)?.int64Value ?? -1,
                                    value: (dict["value"] as? NSNumber)?.uint64Value ?? 0,
                                    hasOffset: dict["hasOffset"] as? Bool ?? false
                                )
                            }.sorted { $0.offset < $1.offset }
                            
                            return
                            
                        } else {
                            print("Could not load plist")
                            return
                        }
                    }
                }
            }
        }

        while output.isEmpty {
            print("Waiting...")
        }
        
        
        return output

       
    }
}
