param(
    [string]$Docx = (Join-Path $PSScriptRoot '..\doc\dokumentation.docx'),
    [string]$Pptx = (Join-Path $PSScriptRoot '..\doc\praesentation.pptx')
)
# Office wird in einem TEMP-Ordner bedient; direkt im OneDrive-Ordner bricht der PDF-Export ab (RPC_E_DISCONNECTED).
$ErrorActionPreference = 'Stop'
$Docx = (Resolve-Path $Docx).Path
$Pptx = (Resolve-Path $Pptx).Path
$tmp = Join-Path $env:TEMP 'spi_doc_export'
New-Item -ItemType Directory -Force $tmp | Out-Null

$wdoc = Join-Path $tmp (Split-Path $Docx -Leaf)
Copy-Item $Docx $wdoc -Force
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($wdoc)
    if ($doc.TablesOfContents.Count -gt 0) { $doc.TablesOfContents.Item(1).Update() }
    $doc.Fields.Update() | Out-Null
    $doc.Save()
    $pdf = [IO.Path]::ChangeExtension($wdoc, '.pdf')
    $doc.ExportAsFixedFormat($pdf, 17)   # wdExportFormatPDF
    'Seiten: ' + $doc.ComputeStatistics(2)
    $doc.Close(0)
} finally { $word.Quit() }
Copy-Item $wdoc $Docx -Force
Copy-Item $pdf ([IO.Path]::ChangeExtension($Docx, '.pdf')) -Force

$wppt = Join-Path $tmp (Split-Path $Pptx -Leaf)
Copy-Item $Pptx $wppt -Force
$ppt = New-Object -ComObject PowerPoint.Application
try {
    $pres = $ppt.Presentations.Open($wppt, $true, $false, $false)
    $pdf2 = [IO.Path]::ChangeExtension($wppt, '.pdf')
    $pres.SaveAs($pdf2, 32)              # ppSaveAsPDF
    'Folien: ' + $pres.Slides.Count
    $pres.Close()
} finally { $ppt.Quit() }
Copy-Item $pdf2 ([IO.Path]::ChangeExtension($Pptx, '.pdf')) -Force
