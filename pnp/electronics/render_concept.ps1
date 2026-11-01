$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$out=$PSScriptRoot
$W=1600;$H=1000
$navy=[System.Drawing.Color]::FromArgb(24,51,77);$blue=[System.Drawing.Color]::FromArgb(32,82,118);$ink=[System.Drawing.Color]::FromArgb(32,42,53);$muted=[System.Drawing.Color]::FromArgb(84,98,112);$pale=[System.Drawing.Color]::FromArgb(243,246,248);$orange=[System.Drawing.Color]::FromArgb(220,117,29);$green=[System.Drawing.Color]::FromArgb(39,132,90);$red=[System.Drawing.Color]::FromArgb(198,78,59)
function NewFont([float]$s,[bool]$bold=$false){$st=if($bold){[System.Drawing.FontStyle]::Bold}else{[System.Drawing.FontStyle]::Regular};[System.Drawing.Font]::new('Arial',$s,$st,[System.Drawing.GraphicsUnit]::Pixel)}
function Txt($g,[string]$t,[int]$x,[int]$y,[float]$size=22,[bool]$bold=$false,[System.Drawing.Color]$color=$ink){$f=NewFont $size $bold;$b=[System.Drawing.SolidBrush]::new($color);$g.DrawString($t,$f,$b,$x,$y);$f.Dispose();$b.Dispose()}
function Box($g,[string]$t,[int]$x,[int]$y,[int]$w,[int]$h,[System.Drawing.Color]$fill=$pale){$b=[System.Drawing.SolidBrush]::new($fill);$p=[System.Drawing.Pen]::new($blue,3);$g.FillRectangle($b,$x,$y,$w,$h);$g.DrawRectangle($p,$x,$y,$w,$h);$a=$t.Split("`n");for($i=0;$i -lt $a.Count;$i++){Txt $g $a[$i] ($x+16) ($y+20+$i*34) $(if($i -eq 0){22}else{17}) ($i -eq 0) $(if($i -eq 0){$ink}else{$muted})};$b.Dispose();$p.Dispose()}
function Save($g,$bmp,[string]$name){$g.Dispose();$bmp.Save((Join-Path $out $name),[System.Drawing.Imaging.ImageFormat]::Png);$bmp.Dispose()}
# Wiring architecture render
$bmp=[System.Drawing.Bitmap]::new($W,$H);$g=[System.Drawing.Graphics]::FromImage($bmp);$g.SmoothingMode='AntiAlias';$g.Clear([System.Drawing.Color]::White)
Txt $g 'TEVO-BW - POWER AND CONTROL ARCHITECTURE' 70 45 34 $true $navy
Box $g "AC INPUT`nswitch / protection" 70 150 250 130;Box $g "LRS-350-24`n24 V / 14.6 A max" 400 150 280 130;Box $g "24 V FUSED BUS`nbranch fuse per load" 770 150 300 130;Box $g "Motion board`n24 V only if rated" 1170 80 340 125;Box $g "Pump + valve`nverify inrush / voltage" 1170 250 340 125
Box $g "DC/DC 24 to 5 V`nservo rail 8 A concept" 770 400 300 130;Box $g "Feeder servos x 8`nexternal power rail" 1170 400 340 130;Box $g "Official USB-C PSU`n5 V / 5 A / 27 W" 770 650 300 130;Box $g "Raspberry Pi 5`nARM64 camera test gate" 1170 650 340 130
$p=[System.Drawing.Pen]::new($red,7);$g.DrawLine($p,320,210,400,210);$g.DrawLine($p,320,250,350,250);$g.DrawLine($p,350,250,350,715);$g.DrawLine($p,350,715,770,715);$p.Color=$orange;$g.DrawLine($p,680,210,770,210);$g.DrawLine($p,1070,185,1120,185);$g.DrawLine($p,1120,140,1120,310);$g.DrawLine($p,1120,140,1170,140);$g.DrawLine($p,1120,310,1170,310);$g.DrawLine($p,920,280,920,400);$g.DrawLine($p,1070,465,1170,465);$p.Color=$green;$g.DrawLine($p,1070,715,1170,715);$p.Dispose()
Txt $g 'PE bonds enclosure, door and PSU. E-stop drops drive power/enable; Pi remains powered for logging.' 70 875 19 $false $muted;Txt $g 'Concept: rate branch fuses, cables and AC protection from measured loads and local code.' 70 910 19 $false $muted
Save $g $bmp 'power_wiring.png'
# Enclosure concept render (perspective shell and component layout)
$bmp=[System.Drawing.Bitmap]::new($W,$H);$g=[System.Drawing.Graphics]::FromImage($bmp);$g.SmoothingMode='AntiAlias';$g.Clear([System.Drawing.Color]::White)
Txt $g 'ELECTRONICS ENCLOSURE - 300 x 240 x 120 mm CONCEPT' 70 45 32 $true $navy
$pts=[System.Drawing.Point[]]@([System.Drawing.Point]::new(170,250),[System.Drawing.Point]::new(920,250),[System.Drawing.Point]::new(1080,155),[System.Drawing.Point]::new(330,155));$face=[System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(244,246,248));$outline=[System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(69,89,102),5);$g.FillPolygon($face,$pts);$g.DrawPolygon($outline,$pts)
$g.FillRectangle([System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(232,237,241)),170,250,750,495);$g.DrawRectangle($outline,170,250,750,495)
$side=[System.Drawing.Point[]]@([System.Drawing.Point]::new(920,250),[System.Drawing.Point]::new(1080,155),[System.Drawing.Point]::new(1080,650),[System.Drawing.Point]::new(920,745));$g.FillPolygon([System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(213,221,227)),$side);$g.DrawPolygon($outline,$side)
$g.FillRectangle([System.Drawing.SolidBrush]::new([System.Drawing.Color]::White),230,300,620,395);$g.DrawRectangle([System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(154,169,180),3),230,300,620,395)
Box $g "24 V PSU`nLRS-350-24`nAC zone / airflow" 270 350 250 145 ([System.Drawing.Color]::FromArgb(255,241,224));Box $g "DIN DC BUS`nfuses / terminals" 565 350 235 145;Box $g "DC/DC 5 V`nservo power" 270 530 250 115;Box $g "Pi 5 BAY`nvented / separated" 565 530 235 115 ([System.Drawing.Color]::FromArgb(234,245,238))
$p=[System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(84,123,50),8);$g.DrawLine($p,205,695,850,695);$p.Dispose();Txt $g 'PE bar / enclosure bond' 265 666 17 $false $muted
Txt $g 'AC gland' 1000 285 17 $false $ink;Txt $g '24 V motor cable' 1000 365 17 $false $ink;Txt $g 'USB / cameras' 1000 445 17 $false $ink
$p=[System.Drawing.Pen]::new($muted,2);$g.DrawLine($p,170,795,920,795);$g.DrawLine($p,170,785,170,805);$g.DrawLine($p,920,785,920,805);$p.Dispose();Txt $g '300 mm' 490 805 22 $true $ink
Txt $g 'Concept arrangement. Keep AC and low-voltage wiring apart; add finger-safe terminals, strain relief and PE bonding.' 170 900 17 $false $muted
Save $g $bmp 'enclosure_render.png'
