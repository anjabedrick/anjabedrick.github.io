// List words the macOS spell checker flags in the given text files: swift spellcheck.swift file...
import AppKit
let checker = NSSpellChecker.shared
checker.setLanguage("en_US")
for path in CommandLine.arguments.dropFirst() {
  var text = try! String(contentsOfFile: path)
  // strip tags, frontmatter keys and URLs
  text = text.replacingOccurrences(of: "<[^>]+>", with: " ", options: .regularExpression)
  text = text.replacingOccurrences(of: "https?://\\S+|/media/\\S+", with: " ", options: .regularExpression)
  var found = Set<String>()
  var r = NSRange(location: 0, length: 0)
  while true {
    r = checker.checkSpelling(of: text, startingAt: r.location + r.length, language: "en_US", wrap: false, inSpellDocumentWithTag: 0, wordCount: nil)
    if r.location == NSNotFound || r.length == 0 { break }
    found.insert((text as NSString).substring(with: r))
  }
  print((path as NSString).lastPathComponent + ": " + found.sorted().joined(separator: ", "))
}
