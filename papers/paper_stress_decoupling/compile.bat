@echo off
echo Compiling Paper 2: Decoupling of Soil vs. Atmospheric Crop Stress...
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
echo.
echo Done! Check main.pdf for output.
