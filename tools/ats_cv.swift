// Build a plain, ATS-friendly CV PDF (one column, real embedded text) from cv/cv-ats.txt.
//   swift tools/ats_cv.swift cv/cv-ats.txt "cv/Anja Bedrick - CV (ATS).pdf"
import AppKit
import CoreText

let args = CommandLine.arguments
let lines = try! String(contentsOfFile: args[1]).components(separatedBy: "\n")
let outURL = URL(fileURLWithPath: args[2]) as CFURL

let page = CGRect(x: 0, y: 0, width: 595, height: 842)  // A4
let margin: CGFloat = 44
let ink = NSColor(calibratedRed: 0.13, green: 0.11, blue: 0.11, alpha: 1)
let grey = NSColor(calibratedWhite: 0.30, alpha: 1)
func font(_ size: CGFloat, bold: Bool = false) -> NSFont {
  NSFont(name: bold ? "Helvetica-Bold" : "Helvetica", size: size) ?? NSFont.systemFont(ofSize: size)
}
func para(spaceBefore: CGFloat = 0, spaceAfter: CGFloat = 0, indent: CGFloat = 0, head: CGFloat = 0, line: CGFloat = 1.15) -> NSParagraphStyle {
  let p = NSMutableParagraphStyle()
  p.paragraphSpacingBefore = spaceBefore; p.paragraphSpacing = spaceAfter
  p.headIndent = indent; p.firstLineHeadIndent = head; p.lineHeightMultiple = line; p.alignment = .left
  return p
}

let doc = NSMutableAttributedString()
func add(_ s: String, _ f: NSFont, _ c: NSColor, _ p: NSParagraphStyle) {
  doc.append(NSAttributedString(string: s + "\n", attributes: [.font: f, .foregroundColor: c, .paragraphStyle: p]))
}
for raw in lines {
  let l = raw.trimmingCharacters(in: .whitespaces)
  if l.isEmpty || l.hasPrefix("#") && !l.hasPrefix("##") { continue }
  if l.hasPrefix("NAME:") { add(String(l.dropFirst(5)).trimmingCharacters(in: .whitespaces), font(20, bold: true), ink, para(spaceAfter: 1)) }
  else if l.hasPrefix("TITLE:") { add(String(l.dropFirst(6)).trimmingCharacters(in: .whitespaces), font(12), ink, para(spaceAfter: 3)) }
  else if l.hasPrefix("CONTACT:") { add(String(l.dropFirst(8)).trimmingCharacters(in: .whitespaces), font(9.5), grey, para(spaceAfter: 2)) }
  else if l.hasPrefix("== ") { add(String(l.dropFirst(3)).uppercased(), font(11, bold: true), ink, para(spaceBefore: 10, spaceAfter: 2)) }
  else if l.hasPrefix("## ") { add(String(l.dropFirst(3)), font(10.5, bold: true), ink, para(spaceBefore: 4, spaceAfter: 0)) }
  else if l.hasPrefix("@ ") { add(String(l.dropFirst(2)), font(9), grey, para(spaceAfter: 2)) }
  else if l.hasPrefix("- ") { add("•\t" + String(l.dropFirst(2)), font(9.5), ink, {
      let p = para(spaceAfter: 1.5, indent: 11) as! NSMutableParagraphStyle
      p.tabStops = [NSTextTab(textAlignment: .left, location: 11)]; return p }()) }
  else { add(l, font(9.5), ink, para(spaceAfter: 2)) }
}

// lay the text out over as many A4 pages as needed
var mediaBox = page
let ctx = CGContext(outURL, mediaBox: &mediaBox, [
  kCGPDFContextTitle: "Anja Bedrick – CV" as CFString, kCGPDFContextAuthor: "Anja Bedrick" as CFString,
  kCGPDFContextCreator: "anjabedrick.com" as CFString] as CFDictionary)!
let setter = CTFramesetterCreateWithAttributedString(doc)
var start = 0
let frameRect = page.insetBy(dx: margin, dy: 30)
repeat {
  ctx.beginPDFPage(nil)
  let path = CGPath(rect: frameRect, transform: nil)
  let frame = CTFramesetterCreateFrame(setter, CFRange(location: start, length: 0), path, nil)
  CTFrameDraw(frame, ctx)
  let visible = CTFrameGetVisibleStringRange(frame)
  start += visible.length
  ctx.endPDFPage()
} while start < doc.length
ctx.closePDF()
print("pages written; characters:", doc.length)
