#import "@preview/haw-hamburg:0.9.0": declaration-of-independent-processing, report

// Register abbreviations and glossary
#import "dependencies.typ": make-glossary, print-glossary, register-glossary
#show: make-glossary
// Abbreviations
#import "abbreviations.typ": abbreviations-entry-list
#register-glossary(abbreviations-entry-list)
// Glossary
#import "glossary.typ": glossary-entry-list
#register-glossary(glossary-entry-list)
// Abstract
#import "abstract.typ": abstract

// Initialize template
#show: report.with(
  language: "de",
  title: "Title",
  author: "Tobias Bandt",
  faculty: "Computer Science",
  // Everything inside "before-content" will be automatically injected
  // into the document before the actual content starts.
  before-content: {
    // Print abstract
    pagebreak(weak: true)
    heading("Abstract", numbering: none)
    abstract

    /*
    // Print abbreviations
    pagebreak(weak: true)
    heading("Abbreviations", numbering: none)
    print-glossary(
      abbreviations-entry-list,
      disable-back-references: true,
    )
    */
  },
  // Everything inside "after-content" will be automatically injected
  // into the document after the actual content ends.
  after-content: {
    /*
    // Print glossary
    pagebreak(weak: true)
    heading("Glossary", numbering: none)
    print-glossary(
      glossary-entry-list,
      disable-back-references: true,
    )

    // Print bibliography
    pagebreak(weak: true)
    bibliography("bibliography.bib", style: "./ieeetran.csl")
    */

    // Declaration of independent processing (comment in to enable)
    declaration-of-independent-processing
  },
)

// Include chapters of report
#pagebreak(weak: true)
#include "chapters/01_einfuehrung.typ"
#include "chapters/02_ausgangszustand.typ"
#include "chapters/03_vorgehen.typ"
#include "chapters/04_durchfuehrung.typ"
#include "chapters/05_ergebnisse.typ"
#include "chapters/06_fazit.typ"
#include "chapters/07_referenzen.typ"
