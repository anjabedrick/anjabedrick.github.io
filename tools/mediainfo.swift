// Print size, duration and bitrate of videos: swift mediainfo.swift a.mp4 b.mp4 ...
import AVFoundation
for p in CommandLine.arguments.dropFirst() {
  let a = AVURLAsset(url: URL(fileURLWithPath: p))
  guard let t = a.tracks(withMediaType: .video).first else { print("no video", p); continue }
  let s = t.naturalSize.applying(t.preferredTransform)
  let mb = Double((try? FileManager.default.attributesOfItem(atPath: p)[.size] as? Int) ?? 0) / 1_048_576
  print(String(format: "%5.1fMB %5.0fx%-5.0f %5.1fs %6.1f Mbps fps%3.0f audio:%@ %@", mb, abs(s.width), abs(s.height), CMTimeGetSeconds(a.duration), t.estimatedDataRate/1e6, t.nominalFrameRate, a.tracks(withMediaType: .audio).isEmpty ? "no" : "yes", (p as NSString).lastPathComponent))
}
