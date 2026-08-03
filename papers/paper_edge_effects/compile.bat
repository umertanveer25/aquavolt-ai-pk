@echo off
echo Compiling Paper 3: Spatial Edge Effects...
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
echo.
echo Done! Check main.pdf for output.
