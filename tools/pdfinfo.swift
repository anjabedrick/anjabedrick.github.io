// Inspect a PDF the way an ATS would: page count, extracted text (reading order), fonts, images.
//   swift pdfinfo.swift file.pdf
import PDFKit
import Quartz
let url = URL(fileURLWithPath: CommandLine.arguments[1])
let doc = PDFDocument(url: url)!
print("pages:", doc.pageCount, "| title:", doc.documentAttributes?[PDFDocumentAttribute.titleAttribute] ?? "-",
      "| author:", doc.documentAttributes?[PDFDocumentAttribute.authorAttribute] ?? "-",
      "| creator:", doc.documentAttributes?[PDFDocumentAttribute.creatorAttribute] ?? "-")
let cg = CGPDFDocument(url as CFURL)!
for p in 1...cg.numberOfPages {
  let page = cg.page(at: p)!
  print("--- page \(p) size:", page.getBoxRect(.mediaBox).size)
  guard let dict = page.dictionary else { continue }
  var res: CGPDFDictionaryRef?
  guard CGPDFDictionaryGetDictionary(dict, "Resources", &res), let r = res else { continue }
  var fonts: CGPDFDictionaryRef?
  if CGPDFDictionaryGetDictionary(r, "Font", &fonts), let f = fonts {
    CGPDFDictionaryApplyBlock(f, { key, obj, _ in
      var fd: CGPDFDictionaryRef?; var name: UnsafePointer<Int8>?
      if CGPDFObjectGetValue(obj, .dictionary, &fd), let d = fd {
        CGPDFDictionaryGetName(d, "BaseFont", &name)
        var sub: UnsafePointer<Int8>?; CGPDFDictionaryGetName(d, "Subtype", &sub)
        var tu: CGPDFStreamRef?; let hasMap = CGPDFDictionaryGetStream(d, "ToUnicode", &tu)
        print("font:", name.map { String(cString: $0) } ?? "?", sub.map { String(cString: $0) } ?? "", hasMap ? "(has ToUnicode map)" : "")
      }
      return true
    }, nil)
  }
  var xo: CGPDFDictionaryRef?
  if CGPDFDictionaryGetDictionary(r, "XObject", &xo), let x = xo {
    CGPDFDictionaryApplyBlock(x, { key, obj, _ in
      var s: CGPDFStreamRef?
      if CGPDFObjectGetValue(obj, .stream, &s), let st = s, let d = CGPDFStreamGetDictionary(st) {
        var sub: UnsafePointer<Int8>?; CGPDFDictionaryGetName(d, "Subtype", &sub)
        var w: CGPDFInteger = 0, h: CGPDFInteger = 0
        CGPDFDictionaryGetInteger(d, "Width", &w); CGPDFDictionaryGetInteger(d, "Height", &h)
        var filt: UnsafePointer<Int8>?; CGPDFDictionaryGetName(d, "Filter", &filt)
        var fmt = CGPDFDataFormat.raw
        let len = (CGPDFStreamCopyData(st, &fmt) as Data?)?.count ?? 0
        print("xobject:", String(cString: key), sub.map { String(cString: $0) } ?? "", "\(w)x\(h)", filt.map { String(cString: $0) } ?? "", "~\(len/1024)KB decoded")
      }
      return true
    }, nil)
  }
}
print("=== extracted text ===")
for i in 0..<doc.pageCount { print(doc.page(at: i)?.string ?? "(no text)") }
