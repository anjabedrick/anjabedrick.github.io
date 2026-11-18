// Pull still frames out of a screen recording: swift frames.swift <video> <outdir> <seconds-between-frames>
import AVFoundation
import AppKit
let asset = AVURLAsset(url: URL(fileURLWithPath: CommandLine.arguments[1]))
let out = CommandLine.arguments[2]; let step = Double(CommandLine.arguments[3])!
let dur = CMTimeGetSeconds(asset.duration); print("duration", dur)
let g = AVAssetImageGenerator(asset: asset); g.appliesPreferredTrackTransform = true
g.maximumSize = CGSize(width: 900, height: 900); g.requestedTimeToleranceBefore = .zero; g.requestedTimeToleranceAfter = .zero
var t = 0.0, i = 0
while t < dur {
  if let cg = try? g.copyCGImage(at: CMTime(seconds: t, preferredTimescale: 600), actualTime: nil) {
    try! NSBitmapImageRep(cgImage: cg).representation(using: .jpeg, properties: [.compressionFactor: 0.6])!.write(to: URL(fileURLWithPath: String(format: "%@/f%03d.jpg", out, i)))
  }
  t += step; i += 1
}
