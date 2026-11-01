$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$out=$PSScriptRoot;$W=1800;$H=1300
$navy=[System.Drawing.Color]::FromArgb(24,51,77);$blue=[System.Drawing.Color]::FromArgb(32,82,118);$ink=[System.Drawing.Color]::FromArgb(32,42,53);$muted=[System.Drawing.Color]::FromArgb(82,98,112);$pale=[System.Drawing.Color]::FromArgb(245,247,248);$orange=[System.Drawing.Color]::FromArgb(220,117,29);$green=[System.Drawing.Color]::FromArgb(39,132,90);$red=[System.Drawing.Color]::FromArgb(198,78,59);$sig=[System.Drawing.Color]::FromArgb(39,108,153);$warn=[System.Drawing.Color]::FromArgb(255,241,224);$safe=[System.Drawing.Color]::FromArgb(234,245,238)
function Font([float]$s,[bool]$b=$false){$st=if($b){[System.Drawing.FontStyle]::Bold}else{[System.Drawing.FontStyle]::Regular};[System.Drawing.Font]::new('Arial',$s,$st,[System.Drawing.GraphicsUnit]::Pixel)}
function Text($g,[string]$t,[int]$x,[int]$y,[float]$s=20,[bool]$b=$false,[System.Drawing.Color]$c=$ink){$f=Font $s $b;$br=[System.Drawing.SolidBrush]::new($c);$g.DrawString($t,$f,$br,$x,$y);$br.Dispose();$f.Dispose()}
function Rect($g,[int]$x,[int]$y,[int]$w,[int]$h,[System.Drawing.Color]$fill=$pale){$br=[System.Drawing.SolidBrush]::new($fill);$p=[System.Drawing.Pen]::new($blue,3);$g.FillRectangle($br,$x,$y,$w,$h);$g.DrawRectangle($p,$x,$y,$w,$h);$br.Dispose();$p.Dispose()}
function Box($g,[string[]]$lines,[int]$x,[int]$y,[int]$w,[int]$h,[System.Drawing.Color]$fill=$pale){Rect $g $x $y $w $h $fill;for($i=0;$i -lt $lines.Count;$i++){Text $g $lines[$i] ($x+14) ($y+12+$i*31) $(if($i -eq 0){20}else{16}) ($i -eq 0) $(if($i -eq 0){$ink}else{$muted})}}
function Wire($g,[int]$x1,[int]$y1,[int]$x2,[int]$y2,[System.Drawing.Color]$c,[float]$w=6){$p=[System.Drawing.Pen]::new($c,$w);$p.StartCap='Square';$p.EndCap='Square';$g.DrawLine($p,$x1,$y1,$x2,$y2);$p.Dispose()}
function StartPage([string]$title){$bmp=[System.Drawing.Bitmap]::new($W,$H);$g=[System.Drawing.Graphics]::FromImage($bmp);$g.SmoothingMode='AntiAlias';$g.Clear([System.Drawing.Color]::White);Text $g $title 55 38 35 $true $navy;return ,@($bmp,$g)}
function SavePage($bmp,$g,[string]$name){Text $g 'CONCEPT ONLY - verify actual hardware, protection and local electrical code before wiring.' 55 1250 16 $false $muted;$g.Dispose();$bmp.Save((Join-Path $out $name),[System.Drawing.Imaging.ImageFormat]::Png);$bmp.Dispose()}

# Terminal-level power and safety schematic
$q=StartPage 'TEVO-BW - terminal-level power wiring';$b=$q[0];$g=$q[1]
Text $g 'A. AC input, protective earth and two independent supplies' 55 95 24 $true $blue
Box $g @('X1 AC IN','L / N / PE','site voltage') 55 145 185 115
Box $g @('Q1 ISOLATOR','2-pole L/N*','PE not switched') 285 145 200 115
Box $g @('F0 AC PROTECT','select per code','rating TBD') 530 145 190 115 $warn
Box $g @('TB-AC','protected L/N','AC distribution') 765 145 215 115
Box $g @('PS1 24V','LRS-350-24','verify input range') 1030 130 250 145 $warn
Box $g @('PS2 HOST PSU','Pi USB-C PSU','or PC supply') 1360 130 300 145 $safe
Wire $g 240 205 285 205 $red;Wire $g 485 205 530 205 $red;Wire $g 720 205 765 205 $red;Wire $g 980 180 1030 180 $red;Wire $g 875 145 875 100 $red;Wire $g 875 100 1485 100 $red;Wire $g 1485 100 1485 130 $red
Box $g @('PE BAR / CHASSIS','X1 PE to cabinet','door bond + PSU FG') 55 290 410 100 $safe;Wire $g 150 260 150 290 $green
Text $g 'B. 24 V branches, E-stop and feeder servo power' 55 405 24 $true $blue
Box $g @('TB24+ / TB0','24 V star point','separate returns') 55 480 220 130
Box $g @('F1 TBD','motion branch') 335 475 160 85 $warn;Box $g @('K1 CONTACT','motion power drop') 545 475 190 85;Box $g @('X4 MOTION','VIN+ / 0V','DRIVER_EN') 785 460 260 115
Box $g @('F2 TBD','vacuum branch') 335 600 160 85 $warn;Box $g @('X5 PUMP / VALVE','check voltage','check inrush') 545 590 250 105
Box $g @('F3 TBD','DC/DC input') 335 735 160 85 $warn;Box $g @('DC/DC1','24 V to 5.0 V','servo rail 8 A target') 545 720 250 115;Box $g @('F4 TBD','servo branch') 845 735 160 85 $warn;Box $g @('X3 IO SHIELD','SERVO V+ / GND','signals D2-D9') 1055 715 265 125 $safe
Wire $g 275 520 335 520 $orange;Wire $g 495 520 545 520 $orange;Wire $g 735 520 785 520 $orange
Wire $g 275 545 305 545 $orange;Wire $g 305 545 305 640 $orange;Wire $g 305 640 335 640 $orange;Wire $g 495 640 545 640 $orange
Wire $g 275 570 315 570 $orange;Wire $g 315 570 315 780 $orange;Wire $g 315 780 335 780 $orange;Wire $g 495 780 545 780 $orange;Wire $g 795 780 845 780 $orange;Wire $g 1005 780 1055 780 $orange
Wire $g 1155 275 1155 440 $orange;Wire $g 1155 440 165 440 $orange;Wire $g 165 440 165 480 $orange
Box $g @('S0 E-STOP','dual NC channels','latching device') 55 750 220 110 $warn;Box $g @('SR1 SAFETY RELAY','drops K1 coil','plus board enable inhibit') 55 905 280 105 $safe;Wire $g 165 860 165 905 $sig;Wire $g 335 955 500 955 $sig;Wire $g 500 955 500 570 $sig;Wire $g 500 570 640 570 $sig;Wire $g 640 570 640 560 $sig
Box $g @('TB0 RETURN','motion / pump / buck','star return, no motor current via logic GND') 1260 905 480 105
Text $g 'F1-F4 are reference IDs, not ratings. Choose protection and conductors from measured loads, module limits and installation rules.' 55 1080 18 $false $muted
Text $g '*Switching of L/N follows local supply rules. PE is continuous, unswitched and unfused.' 55 1120 18 $false $muted
SavePage $b $g 'wiring_detail.png'

# Host / camera / controller topology
$q=StartPage 'TEVO-BW - detailed host and I/O topology';$b=$q[0];$g=$q[1]
Text $g 'Production recommendation: run OpenPnP on x86-64; Pi 5 remains a qualified auxiliary until ARM is proven.' 55 95 22 $true $blue
Box $g @('OPENPNP HOST','x86-64 Linux','USB + Ethernet') 55 185 300 155 $safe
Box $g @('POWERED USB HUB*','certified supply','camera data / USB 3.x') 460 185 320 155
Box $g @('DOWN CAMERA','UVC / MJPEG','stable device ID') 920 125 280 125
Box $g @('UP CAMERA','UVC / MJPEG','stable device ID') 920 285 280 125
Wire $g 355 225 460 225 $sig;Wire $g 780 220 850 220 $sig;Wire $g 850 190 920 190 $sig;Wire $g 850 350 920 350 $sig;Wire $g 850 190 850 350 $sig
Box $g @('MOTION BOARD','USB serial','protocol / VID:PID') 460 470 320 130
Box $g @('ARDUINO NANO','feeder serial','USB powers logic') 920 470 280 130 $warn
Box $g @('8 SERVO PORTS','S1..S8 / GVS','external 5.0 V only') 1320 470 270 130 $safe
Wire $g 355 285 400 285 $sig;Wire $g 400 285 400 520 $sig;Wire $g 400 520 460 520 $sig;Wire $g 355 320 390 320 $sig;Wire $g 390 320 390 640 $sig;Wire $g 390 640 850 640 $sig;Wire $g 850 640 850 535 $sig;Wire $g 850 535 920 535 $sig;Wire $g 1200 520 1320 520 $green
Box $g @('ETHERNET / LAN','wired setup + logs','secure remote access') 55 470 300 130
Wire $g 205 340 205 470 $sig
Box $g @('USB ID CHECK','record VID:PID / serial','bind camera by identity') 55 720 440 145
Box $g @('CAMERA LOAD TEST','both streams together','FPS / format / drops') 565 720 440 145 $warn
Box $g @('ARM HOST GATE','official Linux packages','do not assume ARM64') 1075 720 440 145 $safe
Text $g 'NANO SERVO WIRING: D2->S1, D3->S2, D4->S3, D5->S4, D6->S5, D7->S6, D8->S7, D9->S8.' 55 930 20 $true $ink
Text $g 'External DC/DC 5.0 V -> shield servo V+. DC/DC 0 V -> shield GND. Nano USB VBUS -> logic only; never backfeed external servo V+.' 55 970 18 $false $muted
Text $g 'Verify shield jumper with meter; join signal ground at shield. Powered hub is optional and must be rated for both cameras.' 55 1010 18 $false $muted
Text $g 'OpenPnP Linux packages currently list x86/x64. ARM64 would require a tested application/capture build and two-camera acceptance.' 55 1050 18 $false $muted
SavePage $b $g 'host_io_detail.png'
