#!/bin/bash

# List of subject numbers (edit as needed)
subjects=(1 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21)

# Ensure Text/ folder exists
mkdir -p Text

for id in "${subjects[@]}"; do
  echo "Compiling for Subject $id..."
  pdflatex -interaction=nonstopmode "\def\SubjectNo{$id}\input{20250910_weeklong_individual_summary.tex}"
  
  # Move the PDF into Text/ and rename it
  mv 20250910_weeklong_individual_summary.pdf Text/Subject_${id}_Summary.pdf
done