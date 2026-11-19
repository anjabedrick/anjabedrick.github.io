// Web-optimise videos and GIFs.
//   swift optimize_video.swift video <in.mp4> <out.mp4>   re-encode: H.264, no audio, max 2048px wide, sensible bitrate
//   swift optimize_video.swift gif   <in.gif> <out.mp4>   turn an animated GIF into a silent looping H.264 video
// Bitrate = 0.12 bits per pixel per frame at up to 30fps, 0.07 at 60fps (motion is spread over more frames),
// never above the original. Visually lossless at web display sizes.
import AVFoundation
import ImageIO
import CoreVideo
import AppKit

let args = CommandLine.arguments
let mode = args[1], inPath = args[2], outPath = args[3]
try? FileManager.default.removeItem(atPath: outPath)

func even(_ v: Double) -> Int { max(2, Int(v / 2) * 2) }
func targetSize(_ w: Double, _ h: Double) -> (Int, Int) {
  let scale = min(1, 2048 / max(w, 1))
  return (even(w * scale), even(h * scale))
}
func makeWriter(_ w: Int, _ h: Int, _ bitrate: Double, _ fps: Double) -> (AVAssetWriter, AVAssetWriterInput, AVAssetWriterInputPixelBufferAdaptor) {
  let writer = try! AVAssetWriter(outputURL: URL(fileURLWithPath: outPath), fileType: .mp4)
  let settings: [String: Any] = [
    AVVideoCodecKey: AVVideoCodecType.h264, AVVideoWidthKey: w, AVVideoHeightKey: h,
    AVVideoCompressionPropertiesKey: [AVVideoAverageBitRateKey: Int(bitrate), AVVideoProfileLevelKey: AVVideoProfileLevelH264HighAutoLevel,
                                      AVVideoExpectedSourceFrameRateKey: Int(fps.rounded()), AVVideoMaxKeyFrameIntervalKey: Int(fps.rounded() * 2)],
  ]
  let input = AVAssetWriterInput(mediaType: .video, outputSettings: settings)
  input.expectsMediaDataInRealTime = false
  let adaptor = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: input, sourcePixelBufferAttributes: [
    kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA, kCVPixelBufferWidthKey as String: w, kCVPixelBufferHeightKey as String: h])
  writer.add(input)
  writer.shouldOptimizeForNetworkUse = true  // moov atom first, so playback starts while downloading
  writer.startWriting(); writer.startSession(atSourceTime: .zero)
  return (writer, input, adaptor)
}
func draw(_ img: CGImage, into adaptor: AVAssetWriterInputPixelBufferAdaptor, _ w: Int, _ h: Int, background: CGColor?) -> CVPixelBuffer {
  var pb: CVPixelBuffer?
  CVPixelBufferPoolCreatePixelBuffer(nil, adaptor.pixelBufferPool!, &pb)
  CVPixelBufferLockBaseAddress(pb!, [])
  let ctx = CGContext(data: CVPixelBufferGetBaseAddress(pb!), width: w, height: h, bitsPerComponent: 8,
                      bytesPerRow: CVPixelBufferGetBytesPerRow(pb!), space: CGColorSpaceCreateDeviceRGB(),
                      bitmapInfo: CGImageAlphaInfo.premultipliedFirst.rawValue | CGBitmapInfo.byteOrder32Little.rawValue)!
  if let bg = background { ctx.setFillColor(bg); ctx.fill(CGRect(x: 0, y: 0, width: w, height: h)) }
  ctx.interpolationQuality = .high
  ctx.draw(img, in: CGRect(x: 0, y: 0, width: w, height: h))
  CVPixelBufferUnlockBaseAddress(pb!, [])
  return pb!
}
func finish(_ writer: AVAssetWriter, _ input: AVAssetWriterInput) {
  input.markAsFinished()
  let sem = DispatchSemaphore(value: 0)
  writer.finishWriting { sem.signal() }
  sem.wait()
  if writer.status != .completed { print("FAILED", writer.error as Any); exit(1) }
}

if mode == "gif" {
  let src = CGImageSourceCreateWithURL(URL(fileURLWithPath: inPath) as CFURL, nil)!
  let n = CGImageSourceGetCount(src)
  let first = CGImageSourceCreateImageAtIndex(src, 0, nil)!
  let (w, h) = targetSize(Double(first.width), Double(first.height))
  var delays: [Double] = []
  for i in 0..<n {
    let props = CGImageSourceCopyPropertiesAtIndex(src, i, nil) as? [String: Any]
    let gif = props?[kCGImagePropertyGIFDictionary as String] as? [String: Any]
    var d = (gif?[kCGImagePropertyGIFUnclampedDelayTime as String] as? Double) ?? (gif?[kCGImagePropertyGIFDelayTime as String] as? Double) ?? 0.1
    if d < 0.02 { d = 0.1 }  // browsers treat tiny delays as 0.1s
    delays.append(d)
  }
  let fps = Double(n) / delays.reduce(0, +)
  let (writer, input, adaptor) = makeWriter(w, h, Double(w * h) * max(fps, 12) * 0.12, max(fps, 12))
  var t = 0.0
  // white background: GIF transparency is shown on the page's light backgrounds anyway
  let white = CGColor(red: 1, green: 1, blue: 1, alpha: 1)
  for i in 0..<n {
    let img = CGImageSourceCreateImageAtIndex(src, i, nil)!
    while !input.isReadyForMoreMediaData { usleep(2000) }
    adaptor.append(draw(img, into: adaptor, w, h, background: white), withPresentationTime: CMTime(seconds: t, preferredTimescale: 600))
    t += delays[i]
  }
  // hold the last frame for its full delay
  let last = CGImageSourceCreateImageAtIndex(src, n - 1, nil)!
  while !input.isReadyForMoreMediaData { usleep(2000) }
  adaptor.append(draw(last, into: adaptor, w, h, background: white), withPresentationTime: CMTime(seconds: t - 0.001, preferredTimescale: 600))
  finish(writer, input)
} else {
  let asset = AVURLAsset(url: URL(fileURLWithPath: inPath))
  let track = asset.tracks(withMediaType: .video).first!
  let size = track.naturalSize.applying(track.preferredTransform)
  let (w, h) = targetSize(abs(size.width), abs(size.height))
  let fps = Double(track.nominalFrameRate > 0 ? track.nominalFrameRate : 30)
  let bpp = fps > 40 ? 0.07 : 0.12
  let bitrate = min(Double(track.estimatedDataRate), Double(w * h) * fps * bpp)
  let reader = try! AVAssetReader(asset: asset)
  let comp = AVMutableVideoComposition(propertiesOf: asset)  // applies rotation
  comp.renderSize = CGSize(width: w, height: h)
  let out = AVAssetReaderVideoCompositionOutput(videoTracks: [track], videoSettings: [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA])
  let sx = Double(w) / abs(size.width), sy = Double(h) / abs(size.height)
  let instr = AVMutableVideoCompositionInstruction(); instr.timeRange = CMTimeRange(start: .zero, duration: asset.duration)
  let layer = AVMutableVideoCompositionLayerInstruction(assetTrack: track)
  layer.setTransform(track.preferredTransform.concatenating(CGAffineTransform(scaleX: sx, y: sy)), at: .zero)
  instr.layerInstructions = [layer]; comp.instructions = [instr]
  out.videoComposition = comp
  reader.add(out); reader.startReading()
  let writer = try! AVAssetWriter(outputURL: URL(fileURLWithPath: outPath), fileType: .mp4)
  let input = AVAssetWriterInput(mediaType: .video, outputSettings: [
    AVVideoCodecKey: AVVideoCodecType.h264, AVVideoWidthKey: w, AVVideoHeightKey: h,
    AVVideoCompressionPropertiesKey: [AVVideoAverageBitRateKey: Int(bitrate), AVVideoProfileLevelKey: AVVideoProfileLevelH264HighAutoLevel,
                                      AVVideoMaxKeyFrameIntervalKey: Int(fps.rounded() * 2)]])
  input.expectsMediaDataInRealTime = false
  writer.add(input); writer.shouldOptimizeForNetworkUse = true
  writer.startWriting(); writer.startSession(atSourceTime: .zero)
  while let sample = out.copyNextSampleBuffer() {
    while !input.isReadyForMoreMediaData { usleep(2000) }
    input.append(sample)
  }
  finish(writer, input)
}
let mb = Double((try? FileManager.default.attributesOfItem(atPath: outPath)[.size] as? Int) ?? 0) / 1_048_576
print(String(format: "%.1fMB  %@", mb, (outPath as NSString).lastPathComponent))
