param([string]$OutputPath = (Join-Path $PSScriptRoot 'TEVO_BW_PnP_Dossier.pdf'))
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$W=1240;$PageHeight=1754;$M=88
$navy=[System.Drawing.Color]::FromArgb(24,51,77);$blue=[System.Drawing.Color]::FromArgb(32,82,118);$orange=[System.Drawing.Color]::FromArgb(220,117,29);$ink=[System.Drawing.Color]::FromArgb(32,42,53);$muted=[System.Drawing.Color]::FromArgb(84,98,112);$line=[System.Drawing.Color]::FromArgb(190,201,211);$pale=[System.Drawing.Color]::FromArgb(239,244,248);$warn=[System.Drawing.Color]::FromArgb(255,242,224)
$rasterDir=Join-Path $PSScriptRoot 'full_dossier_raster'
New-Item -ItemType Directory -Force -Path $rasterDir | Out-Null
$annexPages=[System.Collections.Generic.List[string]]::new()
$utf8=[System.Text.UTF8Encoding]::new($false)

function New-Font([float]$Size,[bool]$Bold=$false,[bool]$Mono=$false){$style=if($Bold){[System.Drawing.FontStyle]::Bold}else{[System.Drawing.FontStyle]::Regular};$family=if($Mono){'Consolas'}else{'Arial'};return [System.Drawing.Font]::new($family,$Size,$style,[System.Drawing.GraphicsUnit]::Pixel)}
function Draw-Text($g,[string]$Text,[float]$X,[float]$Y,[float]$Width,[float]$Size=20,[System.Drawing.Color]$Color=$ink,[bool]$Bold=$false,[bool]$Mono=$false){
  if([string]::IsNullOrEmpty($Text)){return 0}
  $font=New-Font $Size $Bold $Mono;$brush=[System.Drawing.SolidBrush]::new($Color);$fmt=[System.Drawing.StringFormat]::new();$fmt.Trimming=[System.Drawing.StringTrimming]::Word
  $measure=$g.MeasureString($Text,$font,[System.Drawing.SizeF]::new($Width,10000),$fmt);$h=[Math]::Ceiling($measure.Height)
  $g.DrawString($Text,$font,$brush,[System.Drawing.RectangleF]::new($X,$Y,$Width,[Math]::Max($h+4,10)),$fmt)
  $font.Dispose();$brush.Dispose();$fmt.Dispose();return $h
}
function New-PlainPage {
  $bmp=[System.Drawing.Bitmap]::new($W,$PageHeight);$bmp.SetResolution(150,150);$g=[System.Drawing.Graphics]::FromImage($bmp);$g.Clear([System.Drawing.Color]::White);$g.SmoothingMode=[System.Drawing.Drawing2D.SmoothingMode]::HighQuality;$g.InterpolationMode=[System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic;$g.TextRenderingHint=[System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
  return ,@($bmp,$g)
}
function Save-Jpeg($bmp,$g,[string]$Path){$g.Dispose();$codec=[System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders()|Where-Object{$_.MimeType -eq 'image/jpeg'}|Select-Object -First 1;$ep=[System.Drawing.Imaging.EncoderParameters]::new(1);$ep.Param[0]=[System.Drawing.Imaging.EncoderParameter]::new([System.Drawing.Imaging.Encoder]::Quality,[long]90);$bmp.Save($Path,$codec,$ep);$ep.Dispose();$bmp.Dispose()}
function New-DocPage([string]$Title){
  if($script:docBmp){Save-DocPage}
  $p=New-PlainPage;$script:docBmp=$p[0];$script:docG=$p[1];$script:docTitle=$Title
  $b=[System.Drawing.SolidBrush]::new($navy);$script:docG.FillRectangle($b,0,0,$W,92);$b.Dispose();Draw-Text $script:docG $Title $M 24 ($W-2*$M) 27 ([System.Drawing.Color]::White) $true|Out-Null
  $script:docG.DrawLine([System.Drawing.Pen]::new($orange,4),$M,105,$W-$M,105);$script:docY=128
}
function Save-DocPage {
  if(-not $script:docBmp){return}
  Draw-Text $script:docG ("TEVO-BW · полный комплект документации · приложение · 01.11.2026") $M 1698 ($W-2*$M) 15 $muted $false|Out-Null
  $path=Join-Path $rasterDir ('annex_{0:D3}.jpg' -f ($annexPages.Count+1));Save-Jpeg $script:docBmp $script:docG $path;$annexPages.Add($path);$script:docBmp=$null;$script:docG=$null
}
function Ensure-DocSpace([float]$Height){if($script:docY+$Height -gt 1648){$t=$script:docTitle;New-DocPage $t}}
function Add-DocText([string]$Text,[float]$Size=18,[System.Drawing.Color]$Color=$ink,[bool]$Bold=$false,[bool]$Mono=$false,[int]$Indent=0,[int]$After=7){
  if([string]::IsNullOrWhiteSpace($Text)){$script:docY+=5;return}
  $width=$W-2*$M-$Indent;$font=New-Font $Size $Bold $Mono;$fmt=[System.Drawing.StringFormat]::new();$fmt.Trimming=[System.Drawing.StringTrimming]::Word;$measure=$script:docG.MeasureString($Text,$font,[System.Drawing.SizeF]::new($width,10000),$fmt);$height=[Math]::Ceiling($measure.Height)+$After
  $font.Dispose();$fmt.Dispose();Ensure-DocSpace $height
  Draw-Text $script:docG $Text ($M+$Indent) $script:docY $width $Size $Color $Bold $Mono|Out-Null;$script:docY+=$height
}
function Add-DocRule {$script:docG.DrawLine([System.Drawing.Pen]::new($line,2),$M,$script:docY,$W-$M,$script:docY);$script:docY+=12}
function Clean-Markdown([string]$Text){
  $s=$Text -replace '!\[([^\]]*)\]\(([^)]*)\)','$1 [image: $2]'
  $s=$s -replace '\[([^\]]+)\]\(([^)]*)\)','$1 ($2)'
  $s=$s -replace '<https?://([^>]+)>','$1'
  $s=$s -replace '`([^`]*)`','$1';$s=$s -replace '\*\*([^*]+)\*\*','$1';$s=$s -replace '__([^_]+)__','$1';$s=$s -replace '\*([^*]+)\*','$1';$s=$s -replace '_([^_]+)_','$1'
  return $s.Trim()
}
function Split-TableLine([string]$Text){$s=$Text.Trim().Trim('|');return @($s -split '\s*\|\s*'|ForEach-Object{$_.Trim()})}
function Add-MarkdownDocument([string]$RelativePath,[string]$Title,[string]$Category){
  $path=Join-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) $RelativePath
  $start=15+$annexPages.Count
  New-DocPage ($Category+' · '+$Title)
  Add-DocText $Title 30 $blue $true $false 0 14
  Add-DocText ('Исходный файл: '+$RelativePath) 15 $muted $false $false 0 15
  $lines=[System.IO.File]::ReadAllLines($path,$utf8);$inCode=$false;$paragraph=[System.Collections.Generic.List[string]]::new();$inTable=$false;$tableHeaders=@()
  foreach($raw in $lines){
    $lineText=[string]$raw
    if($lineText.Trim().StartsWith('```')){
      if($paragraph.Count){Add-DocText ($paragraph -join ' ') 18 $ink $false $false 0 10;$paragraph.Clear()}
      $inCode=-not $inCode;if($inCode){Add-DocRule};continue
    }
    if($inCode){if($lineText.Trim() -ne ''){Add-DocText $lineText 15 $ink $false $true 12 3}else{$script:docY+=4};continue}
    if($lineText -match '^\s*\|.*\|\s*$'){
      if($paragraph.Count){Add-DocText ($paragraph -join ' ') 18 $ink $false $false 0 10;$paragraph.Clear()}
      if($lineText -match '^\s*\|?\s*:?-{3,}'){$inTable=$true;continue}
      $cells=Split-TableLine $lineText
      if(-not $inTable){$tableHeaders=$cells;Add-DocText (($cells -join '  |  ')) 15 $blue $true $false 8 5;$inTable=$true;continue}
      $parts=[System.Collections.Generic.List[string]]::new();for($i=0;$i -lt $cells.Count;$i++){$label=if($i -lt $tableHeaders.Count){$tableHeaders[$i]}else{"Col $($i+1)"};$parts.Add(($label+': '+$cells[$i]))}
      Add-DocText ('• '+($parts -join '   |   ')) 15 $ink $false $false 12 5;continue
    }elseif($inTable){$inTable=$false;$tableHeaders=@();$script:docY+=4}
    if($lineText.Trim() -eq ''){if($paragraph.Count){Add-DocText ($paragraph -join ' ') 18 $ink $false $false 0 11;$paragraph.Clear()};$script:docY+=3;continue}
    if($lineText -match '^\s*[-*_]{3,}\s*$'){if($paragraph.Count){Add-DocText ($paragraph -join ' ') 18 $ink $false $false 0 10;$paragraph.Clear()};Add-DocRule;continue}
    if($lineText -match '^\s*(#{1,6})\s+(.+)$'){
      if($paragraph.Count){Add-DocText ($paragraph -join ' ') 18 $ink $false $false 0 10;$paragraph.Clear()}
      $level=$Matches[1].Length;$text=Clean-Markdown $Matches[2];$size=switch($level){1{27}2{23}3{20}default{18}};Add-DocText $text $size $blue $true $false 0 8;continue
    }
    if($lineText -match '^\s*>\s*(.*)$'){if($paragraph.Count){Add-DocText ($paragraph -join ' ') 18 $ink $false $false 0 10;$paragraph.Clear()};Add-DocText ('NOTE: '+(Clean-Markdown $Matches[1])) 17 $blue $false $false 16 8;continue}
    if($lineText -match '^\s*[-*+]\s+(.+)$'){if($paragraph.Count){Add-DocText ($paragraph -join ' ') 18 $ink $false $false 0 10;$paragraph.Clear()};Add-DocText ('• '+(Clean-Markdown $Matches[1])) 17 $ink $false $false 12 5;continue}
    if($lineText -match '^\s*\d+[.)]\s+(.+)$'){if($paragraph.Count){Add-DocText ($paragraph -join ' ') 18 $ink $false $false 0 10;$paragraph.Clear()};Add-DocText (([regex]::Match($lineText,'^\s*\d+[.)]').Value)+' '+(Clean-Markdown $Matches[1])) 17 $ink $false $false 12 5;continue}
    $clean=Clean-Markdown $lineText;if($clean){$paragraph.Add($clean)}
  }
  if($paragraph.Count){Add-DocText ($paragraph -join ' ') 18 $ink $false $false 0 10;$paragraph.Clear()}
  Save-DocPage
  return [pscustomobject]@{Title=$Title;Start=$start;End=(14+$annexPages.Count);Category=$Category}
}
function Add-CsvDocument([string]$RelativePath,[string]$Title){
  $path=Join-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) $RelativePath;$rows=@(Import-Csv -LiteralPath $path -Encoding UTF8);$start=15+$annexPages.Count
  New-DocPage ('BOM · '+$Title);Add-DocText $Title 30 $blue $true $false 0 8;Add-DocText ('Исходный CSV: '+$RelativePath+' · строк: '+$rows.Count) 15 $muted $false $false 0 15
  if($rows.Count){$headers=@($rows[0].PSObject.Properties.Name);Add-DocText ('Колонки: '+($headers -join '  |  ')) 15 $blue $true $false 0 10
    $n=0;foreach($row in $rows){$n++;$parts=[System.Collections.Generic.List[string]]::new();foreach($h in $headers){$val=[string]$row.$h;if($val){$parts.Add(($h+': '+$val))}};Add-DocText (($n.ToString()+'. ')+($parts -join '   |   ')) 15 $ink $false $false 10 5}
  }
  Save-DocPage;return [pscustomobject]@{Title=$Title;Start=$start;End=(14+$annexPages.Count);Category='BOM'}
}
function Add-ImageCatalogPage([string]$Title,[string]$RelativePath,[string]$Caption){
  $base=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent;$imgPath=Join-Path $base $RelativePath
  $p=New-PlainPage;$bmp=$p[0];$g=$p[1];$bar=[System.Drawing.SolidBrush]::new($navy);$g.FillRectangle($bar,0,0,$W,92);$bar.Dispose();Draw-Text $g $Title $M 25 ($W-2*$M) 27 ([System.Drawing.Color]::White) $true|Out-Null;$g.DrawLine([System.Drawing.Pen]::new($orange,4),$M,105,$W-$M,105)
  $img=[System.Drawing.Image]::FromFile($imgPath);$maxW=$W-2*$M;$maxH=1310;$scale=[Math]::Min($maxW/$img.Width,$maxH/$img.Height);$dw=$img.Width*$scale;$dh=$img.Height*$scale;$x=($W-$dw)/2;$y=125+([Math]::Max(0,$maxH-$dh)/2);$g.DrawImage($img,[System.Drawing.RectangleF]::new($x,$y,$dw,$dh));$img.Dispose()
  Draw-Text $g $Caption $M 1480 ($W-2*$M) 18 $ink $false|Out-Null;Draw-Text $g ('Источник: '+$RelativePath) $M 1550 ($W-2*$M) 15 $muted $false|Out-Null
  $path=Join-Path $rasterDir ('annex_{0:D3}.jpg' -f ($annexPages.Count+1));Save-Jpeg $bmp $g $path;$annexPages.Add($path)
}

# Build the 13-page illustrated overview first. Its raster pages are reused as the opening technical section.
& (Join-Path $PSScriptRoot 'build_dossier.ps1') -OutputPath (Join-Path $rasterDir 'overview_only.pdf') | Out-Null
$overviewDir=Join-Path $PSScriptRoot 'dossier_raster';$overviewPages=@(Get-ChildItem -LiteralPath $overviewDir -Filter 'page_*.jpg'|Sort-Object Name|Select-Object -First 13)
if($overviewPages.Count -ne 13){throw "Expected 13 overview raster pages; found $($overviewPages.Count)."}

$sections=[System.Collections.Generic.List[object]]::new()
$docs=@(
  @('README.md','Project map and getting started','PROJECT'),
  @('TEVO_BW_Pick_and_Place_Technical_Specification.md','Original technical specification (historical baseline)','BASELINE'),
  @('pnp/BUILD_AND_ASSEMBLY.md','Current machine build and assembly guide','MACHINE'),
  @('pnp/README.md','Parametric model and CAD workflow','MACHINE'),
  @('pnp/out/report.md','Generated machine model report and design decisions','MACHINE'),
  @('pnp/feeder/README.md','Feeder v3.0 project guide','FEEDER'),
  @('pnp/feeder/DESIGN.md','Feeder design, mechanisms and limits','FEEDER'),
  @('pnp/feeder/ASSEMBLY.md','Feeder printing and assembly instructions','FEEDER'),
  @('pnp/feeder/ELECTRONICS.md','Feeder controller and servo wiring','FEEDER'),
  @('pnp/feeder/OPENPNP.md','Feeder setup in OpenPnP','FEEDER'),
  @('pnp/feeder/TEST.md','Feeder verification and acceptance procedure','FEEDER'),
  @('pnp/feeder/out/audit.md','Current feeder geometry and design audit','FEEDER'),
  @('pnp/electronics/POWER_CONTROL_DESIGN.md','Machine power and control architecture','ELECTRICAL'),
  @('pnp/electronics/WIRING_DETAILS.md','Terminal schedule and detailed wiring','ELECTRICAL'),
  @('pnp/electronics/PI5_SOFTWARE.md','SBC operating system and OpenPnP software preparation','SOFTWARE'),
  @('pnp/electronics/PROGRESS.md','Engineering progress and remaining gates','PROJECT'),
  @('pnp/out/render/RENDER_STATUS.md','Render revision manifest','PROJECT')
)
foreach($d in $docs){$sections.Add((Add-MarkdownDocument $d[0] $d[1] $d[2]))}
$sections.Add((Add-CsvDocument 'pnp/out/bom.csv' 'Main machine parts list'))
$sections.Add((Add-CsvDocument 'pnp/feeder/out/bom.csv' 'TBW-Feeder v3.0 parts list'))
$sections.Add((Add-CsvDocument 'pnp/electronics/BOM.csv' 'Power and control panel preliminary BOM'))

$imageCatalog=@(
  @('Machine · isometric','pnp/out/render/iso.png','Current project CAD overview; compare physical donor hardware before fabrication.'),
  @('Machine · top view','pnp/out/render/top.png','Working envelope and fixed tooling locations.'),
  @('Machine · front view','pnp/out/render/front.png','Frame, gantry and vertical stack.'),
  @('Machine · side view','pnp/out/render/side.png','Side clearance and motion arrangement.'),
  @('Head · assembly','pnp/out/render/head.png','Current nozzle head and camera geometry.'),
  @('Head · front detail','pnp/out/render/head_front.png','Front detail of Z/C head arrangement.'),
  @('X drive · common shaft','pnp/out/render/xdrive.png','Synchronized dual-belt X drive.'),
  @('Bridge end · rail block','pnp/out/render/bridgeend.png','Bridge end and linear guide interface.'),
  @('Tooling plate','pnp/out/render/table.png','Work plate, datums and support arrangement.'),
  @('Tooling strip','pnp/out/render/strip.png','Fixed feeder/tooling strip and lane arrangement.'),
  @('Feeder v3.0 · current render sheet','pnp/out/render/feeder_sheet.png','Current eight-lane bank, lane mechanism and exploded peel head.'),
  @('Feeder v3.0 · bank in machine','pnp/out/render/feeder.png','Feeder bank generated from the current machine CAD scene.'),
  @('Feeder v3.0 · lane mechanism','pnp/out/render/feeder_mech.png','Servo, rack, idler and one-way roller drive.'),
  @('Feeder v3.0 · peel head exploded','pnp/feeder/out/peel_exploded.png','Current exploded peel head and assembly axis.'),
  @('Power architecture','pnp/electronics/power_wiring.png','Proposed 24 V branches, servo DC/DC and SBC power.'),
  @('Detailed terminal wiring','pnp/electronics/wiring_detail.png','AC/PE, protected DC branches, E-stop and feeder supply.'),
  @('Host, camera and controller I/O','pnp/electronics/host_io_detail.png','OpenPnP host, UVC cameras, motion controller and feeder Nano.'),
  @('Electronics enclosure concept','pnp/electronics/enclosure_render.png','Concept arrangement of PSU, distribution, DC/DC and auxiliary SBC.')
)
$imageStart=15+$annexPages.Count
foreach($im in $imageCatalog){Add-ImageCatalogPage $im[0] $im[1] $im[2]}
$sections.Add([pscustomobject]@{Title='Illustrated render catalog';Start=$imageStart;End=(14+$annexPages.Count);Category='RENDERS'})

# Front cover reused from the compact dossier, followed by a fresh, page-numbered contents sheet.
$cover=$overviewPages[0].FullName
$tocPair=New-PlainPage;$tocBmp=$tocPair[0];$tocG=$tocPair[1];$bb=[System.Drawing.SolidBrush]::new($navy);$tocG.FillRectangle($bb,0,0,$W,102);$bb.Dispose();Draw-Text $tocG 'Содержание · полный комплект документации' $M 27 ($W-2*$M) 31 ([System.Drawing.Color]::White) $true|Out-Null;$tocG.DrawLine([System.Drawing.Pen]::new($orange,5),$M,115,$W-$M,115)
Draw-Text $tocG 'Страницы 1–14: иллюстрированное инженерное резюме. Страницы 15 и далее: исходные руководства и ведомости проекта.' $M 135 ($W-2*$M) 18 $ink $false|Out-Null
$tocY=190
$tocRows=@(
  @('Иллюстрированное инженерное резюме','3–9'),
  @('Питание, компьютер, клеммные схемы и текущий feeder render sheet','10–14')
)
foreach($s in $sections){$tocRows+=,@($s.Title,([string]$s.Start+$(if($s.End -gt $s.Start){'–'+$s.End}else{''}))) }
foreach($row in $tocRows){$title=[string]$row[0];$pg=[string]$row[1];$th=Draw-Text $tocG $title ($M+12) $tocY 820 17 $ink $false;$pw=[Math]::Max(30,$W-$M-20-820);Draw-Text $tocG $pg ($W-$M-100) $tocY 90 17 $blue $true|Out-Null;$tocG.DrawLine([System.Drawing.Pen]::new($line,1),$M+8,$tocY+[Math]::Max($th,22)+7,$W-$M,$tocY+[Math]::Max($th,22)+7);$tocY+=[Math]::Max($th,22)+13}
$tocY+=10;Draw-Text $tocG 'Примечание: техническая спецификация исходной ревизии сохранена как историческая база требований. При расхождениях ориентироваться на актуальные модель, отчёт и руководство сборки. Архивные feeder v2.1 и экспериментальные детали в этот том не включены.' $M $tocY ($W-2*$M) 16 $muted $false|Out-Null
$tocPath=Join-Path $rasterDir 'contents.jpg';Save-Jpeg $tocBmp $tocG $tocPath

# Assemble: cover, contents, overview pages 2-13, then the full documentation annex.
$ordered=[System.Collections.Generic.List[string]]::new();$ordered.Add($cover);$ordered.Add($tocPath)
for($i=1;$i -lt $overviewPages.Count;$i++){$ordered.Add($overviewPages[$i].FullName)}
foreach($p in $annexPages){$ordered.Add($p)}

$ms=[System.IO.MemoryStream]::new();$ascii=[System.Text.Encoding]::ASCII
function WAscii([string]$s){$bytes=$ascii.GetBytes($s);$ms.Write($bytes,0,$bytes.Length)}
function WBytes([byte[]]$bytes){$ms.Write($bytes,0,$bytes.Length)}
function Add-Obj([int]$Id,[string]$Body){$offsets.Add($ms.Position);WAscii ("{0} 0 obj`n{1}`nendobj`n" -f $Id,$Body)}
WAscii "%PDF-1.4`n%TEVO-BW-FULL-DOCUMENTATION`n";$offsets=[System.Collections.Generic.List[long]]::new();$offsets.Add(0)
Add-Obj 1 '<< /Type /Catalog /Pages 2 0 R >>';$kids=for($i=0;$i -lt $ordered.Count;$i++){"$(3+3*$i) 0 R"};Add-Obj 2 ("<< /Type /Pages /Kids [{0}] /Count {1} >>" -f ($kids -join ' '),$ordered.Count)
for($i=0;$i -lt $ordered.Count;$i++){
  $pageId=3+3*$i;$imgId=$pageId+1;$contentId=$pageId+2;$jpg=[System.IO.File]::ReadAllBytes($ordered[$i]);$img=[System.Drawing.Image]::FromFile($ordered[$i]);$iw=$img.Width;$ih=$img.Height;$img.Dispose()
  Add-Obj $pageId ("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /XObject << /Im0 {0} 0 R >> >> /Contents {1} 0 R >>" -f $imgId,$contentId)
  $offsets.Add($ms.Position);WAscii ("{0} 0 obj`n<< /Type /XObject /Subtype /Image /Width {1} /Height {2} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length {3} >>`nstream`n" -f $imgId,$iw,$ih,$jpg.Length);WBytes $jpg;WAscii "`nendstream`nendobj`n"
  $content=$ascii.GetBytes("q`n595 0 0 842 0 0 cm`n/Im0 Do`nQ`n");$offsets.Add($ms.Position);WAscii ("{0} 0 obj`n<< /Length {1} >>`nstream`n" -f $contentId,$content.Length);WBytes $content;WAscii "endstream`nendobj`n"
}
$xref=$ms.Position;WAscii ("xref`n0 {0}`n0000000000 65535 f `n" -f $offsets.Count);for($i=1;$i -lt $offsets.Count;$i++){WAscii ("{0:D10} 00000 n `n" -f $offsets[$i])};WAscii ("trailer`n<< /Size {0} /Root 1 0 R >>`nstartxref`n{1}`n%%EOF`n" -f $offsets.Count,$xref)
[System.IO.File]::WriteAllBytes($OutputPath,$ms.ToArray());$ms.Dispose()
Get-Item $OutputPath | Select-Object FullName,Length,LastWriteTime;Write-Output ("PDF pages: {0}" -f $ordered.Count);Write-Output ("Documentation source files: {0}; render plates: {1}" -f ($docs.Count+3),$imageCatalog.Count)
