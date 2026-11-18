// Contact sheet: swift sheet.swift out.jpg <columns> img1 img2 ...
import AppKit
let args = Array(CommandLine.arguments.dropFirst())
let out = args[0]; let cols = Int(args[1])!; let files = Array(args.dropFirst(2))
let imgs = files.compactMap { NSImage(contentsOfFile: $0) }
let w = 600.0; let h = w * Double(imgs[0].size.height / imgs[0].size.width)
let rows = (imgs.count + cols - 1) / cols
let size = NSSize(width: w * Double(cols), height: (h + 24) * Double(rows))
let canvas = NSImage(size: size); canvas.lockFocus()
NSColor.white.setFill(); NSRect(origin: .zero, size: size).fill()
for (i, im) in imgs.enumerated() {
  let c = i % cols, r = i / cols
  let y = size.height - Double(r + 1) * (h + 24)
  im.draw(in: NSRect(x: Double(c) * w, y: y, width: w - 6, height: h))
  (URL(fileURLWithPath: files[i]).lastPathComponent as NSString).draw(at: NSPoint(x: Double(c) * w + 4, y: y + h + 4), withAttributes: [.font: NSFont.systemFont(ofSize: 16)])
}
canvas.unlockFocus()
try! NSBitmapImageRep(data: canvas.tiffRepresentation!)!.representation(using: .jpeg, properties: [.compressionFactor: 0.7])!.write(to: URL(fileURLWithPath: out))
