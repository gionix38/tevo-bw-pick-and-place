param([string]$OutputPath = (Join-Path $PSScriptRoot 'TEVO_BW_PnP_Dossier.pdf'))
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$W = 1240; $H = 1754; $M = 88
$navy = [System.Drawing.Color]::FromArgb(24,51,77)
$blue = [System.Drawing.Color]::FromArgb(32,82,118)
$orange = [System.Drawing.Color]::FromArgb(220,117,29)
$ink = [System.Drawing.Color]::FromArgb(32,42,53)
$muted = [System.Drawing.Color]::FromArgb(84,98,112)
$line = [System.Drawing.Color]::FromArgb(190,201,211)
$pale = [System.Drawing.Color]::FromArgb(239,244,248)
$warn = [System.Drawing.Color]::FromArgb(255,242,224)
$bad = [System.Drawing.Color]::FromArgb(255,239,236)
$good = [System.Drawing.Color]::FromArgb(235,246,239)
$rasterDir = Join-Path $PSScriptRoot 'dossier_raster'
New-Item -ItemType Directory -Force -Path $rasterDir | Out-Null

function New-Page {
  $b = [System.Drawing.Bitmap]::new($W,$H)
  $b.SetResolution(150,150)
  $g = [System.Drawing.Graphics]::FromImage($b)
  $g.Clear([System.Drawing.Color]::White)
  $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
  $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
  $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
  return ,@($b,$g)
}
function New-Font([float]$Size,[bool]$Bold=$false) {
  $style = if($Bold){[System.Drawing.FontStyle]::Bold}else{[System.Drawing.FontStyle]::Regular}
  return [System.Drawing.Font]::new('Arial',$Size,$style,[System.Drawing.GraphicsUnit]::Pixel)
}
function Draw-Text($g,[string]$Text,[float]$X,[float]$Y,[float]$Width,[float]$Size=22,[System.Drawing.Color]$Color=$ink,[bool]$Bold=$false) {
  $font=New-Font $Size $Bold
  $brush=[System.Drawing.SolidBrush]::new($Color)
  $fmt=[System.Drawing.StringFormat]::new()
  $fmt.Trimming=[System.Drawing.StringTrimming]::Word
  $rect=[System.Drawing.RectangleF]::new($X,$Y,$Width,5000)
  $measure=$g.MeasureString($Text,$font,[System.Drawing.SizeF]::new($Width,5000),$fmt)
  $g.DrawString($Text,$font,$brush,$rect,$fmt)
  $font.Dispose();$brush.Dispose();$fmt.Dispose()
  return [Math]::Ceiling($measure.Height)
}
function Draw-Header($g,[string]$Title,[int]$Page) {
  $brush=[System.Drawing.SolidBrush]::new($navy)
  $g.FillRectangle($brush,0,0,$W,82);$brush.Dispose()
  Draw-Text $g $Title $M 19 ($W-2*$M) 34 ([System.Drawing.Color]::White) $true | Out-Null
  $g.DrawLine([System.Drawing.Pen]::new($orange,5),$M,98,$W-$M,98)
  Draw-Text $g ("TEVO-BW · инженерное досье · 31.10.2026                                  {0} / 13" -f $Page) $M 1698 ($W-2*$M) 16 $muted $false | Out-Null
}
function Draw-Image($g,[string]$Path,[float]$X,[float]$Y,[float]$Width,[float]$Height) {
  $img=[System.Drawing.Image]::FromFile((Resolve-Path (Join-Path $PSScriptRoot $Path)).Path)
  $scale=[Math]::Min($Width/$img.Width,$Height/$img.Height)
  $dw=$img.Width*$scale;$dh=$img.Height*$scale
  $dx=$X+($Width-$dw)/2;$dy=$Y+($Height-$dh)/2
  $g.DrawImage($img,[System.Drawing.RectangleF]::new($dx,$dy,$dw,$dh))
  $img.Dispose()
}
function Draw-Section($g,[string]$Text,[float]$Y) {
  Draw-Text $g $Text $M $Y ($W-2*$M) 28 $blue $true | Out-Null
  return ($Y+45)
}
function Draw-Paragraph($g,[string]$Text,[float]$Y,[float]$Width=1060,[float]$Size=21,[System.Drawing.Color]$Color=$ink) {
  $h=Draw-Text $g $Text $M $Y $Width $Size $Color $false
  return ($Y+$h+12)
}
function Draw-Bullet($g,[string]$Text,[float]$Y,[float]$Width=1060,[float]$Size=20) {
  $h=Draw-Text $g ('• '+$Text) ($M+4) $Y ($Width-4) $Size $ink $false
  return ($Y+$h+9)
}
function Draw-Table($g,[string[]]$Headers,[object[]]$Rows,[float[]]$Widths,[float]$Y,[float]$Size=17) {
  $x0=$M; $pad=9; $headFont=New-Font ($Size+1) $true; $cellFont=New-Font $Size $false
  $fmt=[System.Drawing.StringFormat]::new();$fmt.Trimming=[System.Drawing.StringTrimming]::Word
  $white=[System.Drawing.SolidBrush]::new([System.Drawing.Color]::White)
  $dark=[System.Drawing.SolidBrush]::new($navy);$alt=[System.Drawing.SolidBrush]::new($pale)
  $black=[System.Drawing.SolidBrush]::new($ink);$pen=[System.Drawing.Pen]::new($line,1)
  $hh=45;$x=$x0
  for($c=0;$c -lt $Headers.Count;$c++){$g.FillRectangle($dark,$x,$Y,$Widths[$c],$hh);$g.DrawString($Headers[$c],$headFont,$white,[System.Drawing.RectangleF]::new($x+$pad,$Y+8,$Widths[$c]-2*$pad,$hh-10),$fmt);$x+=$Widths[$c]}
  $Y+=$hh
  foreach($row in $Rows){
    $cells=@($row);$rh=42
    for($c=0;$c -lt $cells.Count;$c++){$ms=$g.MeasureString([string]$cells[$c],$cellFont,[System.Drawing.SizeF]::new($Widths[$c]-2*$pad,800),$fmt);$rh=[Math]::Max($rh,[Math]::Ceiling($ms.Height)+2*$pad)}
    $x=$x0
    for($c=0;$c -lt $cells.Count;$c++){$g.FillRectangle($alt,$x,$Y,$Widths[$c],$rh);$g.DrawRectangle($pen,$x,$Y,$Widths[$c],$rh);$g.DrawString([string]$cells[$c],$cellFont,$black,[System.Drawing.RectangleF]::new($x+$pad,$Y+$pad,$Widths[$c]-2*$pad,$rh-2*$pad),$fmt);$x+=$Widths[$c]}
    $Y+=$rh
  }
  $headFont.Dispose();$cellFont.Dispose();$fmt.Dispose();$white.Dispose();$dark.Dispose();$alt.Dispose();$black.Dispose();$pen.Dispose()
  return ($Y+15)
}
function Draw-Box($g,[string]$Text,[float]$X,[float]$Y,[float]$Width,[float]$Height,[System.Drawing.Color]$Fill=$pale) {
  $Text=$Text.Replace('`n',[Environment]::NewLine)
  $b=[System.Drawing.SolidBrush]::new($Fill);$p=[System.Drawing.Pen]::new($blue,2)
  $g.FillRectangle($b,$X,$Y,$Width,$Height);$g.DrawRectangle($p,$X,$Y,$Width,$Height)
  Draw-Text $g $Text ($X+8) ($Y+8) ($Width-16) 18 $ink $true | Out-Null
  $b.Dispose();$p.Dispose()
}
function Save-Page($bitmap,[int]$Number) {
  $path=Join-Path $rasterDir ('page_{0:D2}.jpg' -f $Number)
  $codec=[System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object {$_.MimeType -eq 'image/jpeg'} | Select-Object -First 1
  $params=[System.Drawing.Imaging.EncoderParameters]::new(1)
  $params.Param[0]=[System.Drawing.Imaging.EncoderParameter]::new([System.Drawing.Imaging.Encoder]::Quality,[long]88)
  $bitmap.Save($path,$codec,$params);$params.Dispose();$bitmap.Dispose()
  return $path
}

$pages=[System.Collections.Generic.List[string]]::new()

# 1 Cover and hero render
$q=New-Page;$b=$q[0];$g=$q[1]
$band=[System.Drawing.SolidBrush]::new($navy);$g.FillRectangle($band,0,0,$W,215);$band.Dispose()
Draw-Text $g 'TEVO BLACK WIDOW' $M 34 1060 30 ([System.Drawing.Color]::FromArgb(244,168,85)) $true | Out-Null
Draw-Text $g 'Инженерное досье' $M 85 1060 53 ([System.Drawing.Color]::White) $true | Out-Null
Draw-Text $g 'Компоновка · сборка · расчётные проверки · риски' $M 151 1060 25 ([System.Drawing.Color]::White) $false | Out-Null
Draw-Image $g 'render/iso.png' 55 245 1130 970
Draw-Text $g 'CAD-рендер текущей компоновки. Плата и feeder bank неподвижны; портал движется по X, каретка — по Y.' $M 1227 1060 17 $muted $false | Out-Null
Draw-Box $g 'ХОД X/Y`n453 × 382,6 мм' 90 1300 320 105 $pale
Draw-Box $g 'ПОДАТЧИКИ`n8 дорожек, шаг 22 мм' 460 1300 320 105 $pale
Draw-Box $g 'МАССА ГОЛОВЫ`n499 г по модели / 500 г бюджет' 830 1300 320 105 $warn
$y=Draw-Paragraph $g 'Предварительная оценка по исходникам проекта и CAD-отчёту. Геометрическая проверка столкновений не доказывает жёсткость, точность или ресурс физической машины.' 1440 1060 20
Draw-Text $g 'Редакция 0.1 · 31 октября 2026 · TEVO_BW' $M 1610 1060 17 $muted $false | Out-Null
$pages.Add((Save-Page $b 1))

# 2 Layout
$q=New-Page;$b=$q[0];$g=$q[1];Draw-Header $g '1 · Архитектура и компоновка' 2
$y=Draw-Paragraph $g 'Две C-Beam балки уложены горизонтально и работают как X-рельсы. Профиль 40×80×550 мм образует подвижную Y-балку. Рабочая плита, PCB, камеры, магазин и ленты остаются неподвижными.' 118
Draw-Image $g 'render/top.png' $M $y 1060 790
$y+=800;Draw-Text $g 'Вид сверху: инструменты вынесены за правую границу хода портала.' $M $y 1060 17 $muted $false | Out-Null;$y+=35
$rows=@(
  @('X','Две MGN12, два GT2 ремня и общий вал 8 мм','Синхронность ремней и yaw портала'),
  @('Y','MGN12 и штатный ременной привод на балке 40×80','Боковое качание головы и тяга цепи'),
  @('Z / C','NEMA8 linear T5×2; NEMA8 hollow-shaft на оси сопла','Перекос Z, люфт, биение наконечника'),
  @('Tooling','Плита 635×444×6 мм на трёх опорах','Плоскостность PCB и прогиб выноса')
)
Draw-Table $g @('Узел','Реализация','Что проверить') $rows @(125,480,455) $y 16 | Out-Null
$pages.Add((Save-Page $b 2))

# 3 Assembly overview and drive details
$q=New-Page;$b=$q[0];$g=$q[1];Draw-Header $g '2 · Сборочная схема машины' 3
$y=125
$labels=@('1  Основание`nC-Beam + угловые блоки`nпоперечины → выверка','2  Портал X`nMGN12 + торцы`nбалка + два ремня','3  Каретка Y`nрельс + ремень`nголова + drag chain','4  Рабочий стол`n3 точки опоры`nPCB datum + зажим','5  Оснастка`n8 feeders + камеры`nмагазин сопел','6  Пуск`nmotion board + Nano`nOpenPnP и калибровка')
for($i=0;$i -lt 3;$i++){Draw-Box $g $labels[$i] (90+$i*370) $y 330 125 $(if($i -eq 0){$warn}else{$pale})}
$y+=155;Draw-Text $g 'Сначала выставить базу и рельсы; ремни натягивать после проверки свободного хода.' $M $y 1060 19 $ink $true | Out-Null
$y+=50;Draw-Image $g 'render/xdrive.png' $M $y 510 620;Draw-Image $g 'render/bridgeend.png' 635 $y 515 620
$y+=635;Draw-Text $g 'Слева: общий вал и X-привод. Справа: мостовой торец на MGN12H и крепление к балке.' $M $y 1060 17 $muted $false | Out-Null
$y+=42
$rows=@(@('Рама','Измерить диагонали, зазор C-Beam, плоскость крепления рельсов.'),@('Портал','Свести фазу ремней; измерить перекос на обоих концах хода.'),@('Каретка','Проверить ход без заедания и повторить измерения с установленной головой.'))
Draw-Table $g @('Этап','Контроль перед продолжением') $rows @(180,880) $y 17 | Out-Null
$pages.Add((Save-Page $b 3))

# 4 Head
$q=New-Page;$b=$q[0];$g=$q[1];Draw-Header $g '3 · Голова и размерная цепь' 4
$y=120;Draw-Image $g 'render/head.png' $M $y 1060 760
$y+=775;Draw-Text $g 'Схема сборки головы (последовательность, не взрывной CAD-вид)' $M $y 1060 22 $blue $true | Out-Null
$y+=55
Draw-Box $g 'Y-блоки`nMGN12' 90 $y 185 105 $pale;Draw-Box $g 'Каретка`nPETG-CF' 300 $y 185 105 $warn;Draw-Box $g 'Z rail + slide`nMGN9 / Al' 510 $y 185 105 $pale;Draw-Box $g 'C motor`nhollow shaft' 720 $y 185 105 $pale;Draw-Box $g 'Compliance`n+ nozzle' 930 $y 185 105 $good
$y+=130
$rows=@(@('Z','NEMA8 linear actuator, винт T5×2, фланцевая гайка','Измерить Z perpendicularity, backlash и повторяемость home.'),@('C','NEMA8 hollow-shaft, вакуум через ось','Измерить TIR наконечника по обороту и при боковой нагрузке.'),@('Vision','Down camera смещена на (2,57) мм от сопла','Калибровать offset по нескольким реперным точкам.'))
Draw-Table $g @('Подсистема','Модель','Проверка') $rows @(135,440,485) $y 16 | Out-Null
$pages.Add((Save-Page $b 4))

# 5 feeder exploded
$q=New-Page;$b=$q[0];$g=$q[1];Draw-Header $g '4 · Податчик TBW-Feeder v3.0' 5
$y=118;Draw-Paragraph $g 'Ниже — настоящий CAD-взрывной вид peel head. Ориентация двух обгонных подшипников HF0612 определяет, какой ролик тянет ленту, а какой удерживает натяжение на обратном ходе.' $y 1060 19 | Out-Null
Draw-Image $g '../feeder/out/peel_exploded.png' $M 210 1060 870
$y=1095;Draw-Text $g 'Кинематические цепи' $M $y 1060 24 $blue $true | Out-Null;$y+=47
Draw-Box $g 'Серво`nMG90S' 90 $y 200 90 $pale;Draw-Box $g 'Сектор 13T`n+ слайдер' 325 $y 200 90 $pale;Draw-Box $g 'Рейка +`n36T idler' 560 $y 200 90 $pale;Draw-Box $g '14T pinion`n+ HF0612' 795 $y 200 90 $pale;Draw-Box $g 'Peel roller`n+ nip → bin' 1030 $y 120 90 $good
$y+=110
Draw-Paragraph $g 'Отдельный пружинный pawl перемещает carrier tape на F2/F4; detent фиксирует следующий шаг. Одна дорожка проходит физические тесты до изготовления оставшихся семи.' $y 1060 19 | Out-Null
$pages.Add((Save-Page $b 5))

# 6 calculations
$q=New-Page;$b=$q[0];$g=$q[1];Draw-Header $g '5 · Кинематика и динамика' 6
$y=125;Draw-Text $g 'Шаги на единицу — при заданных двигателях, шкивах и микрошаге:' $M $y 1060 21 $ink $false | Out-Null;$y+=45
$rows=@(
  @('XY','200 × 16 / (2 мм × 20T)','80 steps/mm'),
  @('Z','200 × 4 / 2 мм lead','400 steps/mm'),
  @('C','200 × 16 / 360°','8,8889 steps/°'),
  @('X torque margin','0,252 / 0,088 N·m; базовый расчёт 24 В','2,9'),
  @('Y torque margin','0,252 / 0,042 N·m; базовый расчёт 24 В','6,1'),
  @('Цикл PR-10','4,97 с/шт; 3600 / 4,97','724 шт/ч; до 814 при перекрытии подачи')
)
$y=Draw-Table $g @('Проверка','Расчёт','Результат модели') $rows @(205,470,385) $y 18
$y=Draw-Section $g 'Ходы и рабочие пределы' $y
Draw-Box $g 'X travel`n453 мм' 90 $y 320 100 $pale;Draw-Box $g 'Y travel`n382,6 мм' 460 $y 320 100 $pale;Draw-Box $g 'Z usable`n35 мм' 830 $y 320 100 $pale
$y+=125
$y=Draw-Paragraph $g 'Модель считает X: 3,08 кг при 3000 мм/с² и 400 мм/с; Y: около 0,50 кг при 4000 мм/с². Для torque curve используется PSU 24 В и типовой NEMA17. При 12 В отчёт указывает запас X около 1,9 — ниже проектного коэффициента 2.' $y 1060 20
$y=Draw-Paragraph $g 'PR-10: базовый расчёт 724 шт/ч не достигает цели 800 шт/ч; вариант с перекрытием подачи даёт 814 шт/ч только по оценке модели. Цикл на реальной машине не измерен.' $y 1060 20 $muted
$y=Draw-Section $g 'Границы расчёта' $y
$y=Draw-Bullet $g 'Нет FEA и modal analysis, нет проверки bolt preload или деформации печатных деталей.' $y
$y=Draw-Bullet $g 'Каталожные массы/моменты, фактический драйвер и усилие кабельной цепи ещё не измерены.' $y | Out-Null
$pages.Add((Save-Page $b 6))

# 7 design audit
$q=New-Page;$b=$q[0];$g=$q[1];Draw-Header $g '6 · Слабые места и меры усиления' 7
$rows=@(
  @('P0 · Стол','Плита 635×444×6 мм, около 4,5 кг, три опоры; прогиб не посчитан.','Снять карту плоскости PCB-индикатором; добавить нижние рёбра/опорные профили, сохранив кинематические три точки.'),
  @('P0 · Углы рамы','Печатные PETG/ASA блоки совмещают опору, привод/подшипник, tie и ногу.','Металлические пластины/кронштейны в силовой цепи X-мотора и опор вала; контроль соосности после натяжения.'),
  @('P0 · Масса головы','499 г при лимите 500 г; расчётный запас 1 г.','Взвесить голову вместе с проводами и вакуумным шлангом; обновить модель.'),
  @('P1 · Портал','Один MGN12H на каждом X-рельсе, стойки портала 32 мм; моменты не рассчитаны.','Измерить прогиб/качание на крайних позициях; проверить моментные рейтинги блока и креплений.'),
  @('P1 · Питание','Расчёт движения основан на 24 В; при 12 В запас X ниже цели.','Подтвердить PSU, ток моторов и драйвер; разгонять только после тестов на потерю шагов.'),
  @('P1 · Камера lane 1','Расчётная камера имеет примерно 5,5 мм запаса до края Y-хода.','Физически проверить предел, кронштейн и допуски; при необходимости сдвинуть узел.'),
  @('P1 · C-axis','Hollow-shaft мотор задаёт биение сопла; выбранный экземпляр не подтверждён.','Измерить runout наконечника; при превышении допуска добавить отдельную прецизионную опору.')
)
$y=Draw-Table $g @('Риск','Наблюдение по CAD/расчёту','Что сделать до полной сборки') $rows @(180,430,450) 125 16
$y=Draw-Section $g 'Общая оценка компоновки' ($y+5)
Draw-Paragraph $g 'Размещение логичное: плата и ленты неподвижны; feeder bank находится вне траектории балки; общий вал синхронизирует X. Главные неопределённости относятся к жёсткости, деформации, вибрациям и метрологии, а не к базовой логике расположения узлов.' ($y+3) 1060 20 $blue | Out-Null
$pages.Add((Save-Page $b 7))

# 8 assembly gates and acceptance
$q=New-Page;$b=$q[0];$g=$q[1];Draw-Header $g '7 · План сборки и приёмки' 8
$rows=@(
  @('1','Обмер до разборки','PSU/плата/драйверы, геометрия рамы, плоскость стола и фотографии разъёмов.'),
  @('2','Рама и база','Диагонали, параллельность рельсов, плоскость tooling plate и повторяемость измерений.'),
  @('3','Портал/каретка','Натяжение двух X-ремней, yaw, полный ход, прогиб под массой головы.'),
  @('4','Голова','Фактическая масса; Z perpendicularity/home; C runout; nozzle-to-camera offset.'),
  @('5','Feeder first article','Одна дорожка: канал, подача F2/F4, peel, удержание, endurance из feeder/TEST.md.'),
  @('6','Электрика и OpenPnP','Отдельные контроллеры motion и feeder; проверки E-stop, vacuum, камеры, Safe Z.'),
  @('7','Приёмка','PR-8 размещение 0603, PR-10 цикл, PR-11 lost picks, PR-12 homing — записать измерения.')
)
Draw-Table $g @('#','Сборочный этап','Выходной контроль') $rows @(70,250,740) 125 17 | Out-Null
$y=Draw-Section $g 'Подтверждено / не подтверждено' 890
Draw-Box $g 'CAD-ПРОВЕРЕНО`nReach по рассчитанной геометрии; отсутствие пересечений на выбранных позах; расчётная кинематика и BOM.' 90 $y 510 180 $good
Draw-Box $g 'НУЖНО ИЗМЕРИТЬ`nПлоскость, прогиб, вибрации, реальный torque margin, runout сопла, repeatability, feeder endurance и placement scatter.' 635 $y 510 180 $warn
$y+=205
$y=Draw-Paragraph $g 'Сборку полного станка начинать после проверки actual donor hardware и ревизии спецификации. Опорные документы: pnp/BUILD_AND_ASSEMBLY.md, pnp/out/report.md, pnp/feeder/ASSEMBLY.md, ELECTRONICS.md, OPENPNP.md, TEST.md.' $y 1060 21
Draw-Text $g 'Документ подготовлен по файлам проекта D:\TEVO_BW; CAD-рендеры взяты из pnp/out/render и pnp/feeder/out.' $M 1600 1060 16 $muted $false | Out-Null
$pages.Add((Save-Page $b 8))

# 9 power and control architecture
$q=New-Page;$b=$q[0];$g=$q[1];Draw-Header $g '8 · Питание и компьютер управления' 9
$y=118;Draw-Paragraph $g 'Проектное решение: общая 24 V шина для motion board и периферии после проверки их паспортов; отдельный DC/DC 24→5 V для сервоприводов; Raspberry Pi 5 питается своим официальным USB-C БП. Feeder Nano остаётся независимым USB serial контроллером.' $y 1060 19
Draw-Image $g '../electronics/power_wiring.png' $M 255 1060 790
$y=1055
$rows=@(
  @('24 V PSU','LRS-350-24, 14.6 A / 350.4 W max','Только предварительный выбор; подтвердить суммарную нагрузку и совместимость платы.'),
  @('Motion / vacuum','Раздельные ветви с защитой','Номиналы защит и кабелей выбрать по фактическим платам, току и пуску насоса.'),
  @('Feeder servos','24→5 V, целевой DC/DC ≥8 A','Не питать сервоприводы через Pi, Nano или USB; проверить stall/просадку.'),
  @('Host','x86-64 mini-PC is production recommendation; Pi 5 optional auxiliary','Official OpenPnP Linux packages list x86/x64. Pi/Orange ARM64 requires a tested custom build and two-camera qualification.')
)
Draw-Table $g @('Узел','Концепция','Условие до сборки') $rows @(180,380,500) $y 15 | Out-Null
$y=Draw-Paragraph $g 'E-stop снимает аппаратный DRIVER_EN и питание приводов; SBC остаётся включённым для журнала. PE соединяет металлический корпус, дверь и PE источника. Все сетевые защиты, сечения и клеммы уточнить по шильдикам и местным нормам.' 1510 1060 17 $muted
$pages.Add((Save-Page $b 9))

# 10 enclosure render and bring-up gates
$q=New-Page;$b=$q[0];$g=$q[1];Draw-Header $g '9 · Корпус блока и ввод в эксплуатацию' 10
$y=125;Draw-Paragraph $g 'Компоновочный конверт 300×240×120 мм. На картинке показаны зоны размещения: PSU и сетевой ввод, защищённая DC-разводка, отдельный 5 V buck, SBC в охлаждаемом низковольтном отсеке, вводы кабелей и шина PE.' $y 1060 19
Draw-Image $g '../electronics/enclosure_render.png' $M 250 1060 900
$y=1180
$rows=@(
  @('1','Сверить donor board, drivers и маркировку всех нагрузок; подтвердить 12/24 V.'),
  @('2','Проверить полярность и выставить 24.0 V / 5.0 V с ограничением тока.'),
  @('3','Проверить E-stop без движения: аппаратный запрет приводов, Pi остаётся online.'),
  @('4','Проверить Nano и сервошину отдельно, затем измерить просадку на дальнем servo.'),
  @('5','На x86-64 host проверить OpenPnP, обе камеры и serial motion/feeder; Pi ARM64 оставить экспериментальным.'),
  @('6','Тепловой прогон 30 минут; записать температуры, напряжения, brownout и сбросы.')
)
Draw-Table $g @('#','Пусковой контроль') $rows @(70,990) $y 16 | Out-Null
Draw-Paragraph $g 'Эскиз не является производственным чертежом. Уточнить габариты/зазоры по реальным компонентам и обеспечить закрытые клеммы, strain relief, вентиляцию, PE bonding и разделение AC/DC.' $M 1610 1060 16 $muted | Out-Null
$pages.Add((Save-Page $b 10))

# 11 terminal-level wiring
$q=New-Page;$b=$q[0];$g=$q[1];Draw-Header $g '10 · Подробная клеммная схема питания' 11
$y=118;Draw-Paragraph $g 'Схема показывает назначение коннекторов X1-X5, распределение AC/PE/24 V, идентификаторы ответвлений F1-F4, E-stop и отдельную 5 V сервошину. Номиналы F0-F4 намеренно оставлены TBD до идентификации реальных нагрузок и проводов.' $y 1060 18
Draw-Image $g '../electronics/wiring_detail.png' $M 235 1060 850
$y=1110
Draw-Paragraph $g 'Возврат моторов и насоса вести отдельными проводами на TB0; не пропускать рабочий ток через логику Nano/Pi. PE непрерывен, без предохранителя и коммутации. Перед подключением плат прозвонить X3/X4/X5, проверить полярность и отсутствие перемычки между внешним servo V+ и USB VBUS.' $y 1060 18
$pages.Add((Save-Page $b 11))

# 12 host, camera and feeder I/O detail
$q=New-Page;$b=$q[0];$g=$q[1];Draw-Header $g '11 · Host, камеры и USB' 12
$y=118;Draw-Paragraph $g 'Производственный host — x86-64 mini-PC с Linux 64-bit и официальной OpenPnP Linux сборкой. Raspberry Pi 5/Orange Pi с ARM64 можно использовать как вспомогательную плату; запуск OpenPnP на ARM требует отдельной сборки и квалификации.' $y 1060 18
Draw-Image $g '../electronics/host_io_detail.png' $M 240 1060 830
$y=1110
Draw-Paragraph $g 'Nano: D2-D9 управляют дорожками 1-8. USB питает только логику; DC/DC1 питает сервошину через отдельный вход shield. Камеры назначать по устойчивому device ID и проверять одновременно под выбранной частотой кадров.' $y 1060 18
Draw-Paragraph $g 'Порядок подготовки Pi OS, SHA-256 официального образа, ссылки на OpenPnP и результаты сетевой попытки скачивания записаны в pnp/electronics/PI5_SOFTWARE.md.' ($y+75) 1060 16 $muted | Out-Null
$pages.Add((Save-Page $b 12))

# 13 updated current feeder render sheet
$q=New-Page;$b=$q[0];$g=$q[1];Draw-Header $g '12 · TBW-Feeder v3.0: свежие CAD-рендеры' 13
$y=118;Draw-Paragraph $g 'Лист собран из обновлённых FreeCAD-рендеров: feeder bank в контексте машины, механизм одной дорожки и отдельный взрывной peel head.' $y 1060 19
Draw-Image $g 'render/feeder_sheet.png' $M 205 1060 1000
$y=1270
Draw-Paragraph $g 'Исходные виды: render/feeder.png и render/feeder_mech.png; взрывной вид: feeder/out/peel_exploded.png. Все четыре файла перегенерированы из текущей геометрии v3.0 31.10.2026.' $y 1060 17 $muted | Out-Null
$pages.Add((Save-Page $b 13))

# Build a compact image-based PDF (all typography is rasterized with Arial for consistent Cyrillic rendering).
$ms=[System.IO.MemoryStream]::new();$ascii=[System.Text.Encoding]::ASCII
function WAscii([string]$s){$bytes=$ascii.GetBytes($s);$ms.Write($bytes,0,$bytes.Length)}
function WBytes([byte[]]$bytes){$ms.Write($bytes,0,$bytes.Length)}
WAscii "%PDF-1.4`n%TEVO-BW`n"
$offsets=[System.Collections.Generic.List[long]]::new();$offsets.Add(0)
function Add-Obj([int]$Id,[string]$Body){$offsets.Add($ms.Position);WAscii ("{0} 0 obj`n{1}`nendobj`n" -f $Id,$Body)}
Add-Obj 1 '<< /Type /Catalog /Pages 2 0 R >>'
$kids=for($i=0;$i -lt $pages.Count;$i++){"$(3+3*$i) 0 R"}
Add-Obj 2 ("<< /Type /Pages /Kids [{0}] /Count {1} >>" -f ($kids -join ' '),$pages.Count)
for($i=0;$i -lt $pages.Count;$i++){
  $pageId=3+3*$i;$imgId=$pageId+1;$contentId=$pageId+2
  $jpg=[System.IO.File]::ReadAllBytes($pages[$i])
  Add-Obj $pageId ("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /XObject << /Im0 {0} 0 R >> >> /Contents {1} 0 R >>" -f $imgId,$contentId)
  $offsets.Add($ms.Position);WAscii ("{0} 0 obj`n<< /Type /XObject /Subtype /Image /Width {1} /Height {2} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length {3} >>`nstream`n" -f $imgId,$W,$H,$jpg.Length);WBytes $jpg;WAscii "`nendstream`nendobj`n"
  $content=$ascii.GetBytes("q`n595 0 0 842 0 0 cm`n/Im0 Do`nQ`n")
  $offsets.Add($ms.Position);WAscii ("{0} 0 obj`n<< /Length {1} >>`nstream`n" -f $contentId,$content.Length);WBytes $content;WAscii "endstream`nendobj`n"
}
$xref=$ms.Position;WAscii ("xref`n0 {0}`n0000000000 65535 f `n" -f $offsets.Count)
for($i=1;$i -lt $offsets.Count;$i++){WAscii ("{0:D10} 00000 n `n" -f $offsets[$i])}
WAscii ("trailer`n<< /Size {0} /Root 1 0 R >>`nstartxref`n{1}`n%%EOF`n" -f $offsets.Count,$xref)
[System.IO.File]::WriteAllBytes($OutputPath,$ms.ToArray());$ms.Dispose()
Get-Item $OutputPath | Select-Object FullName,Length,LastWriteTime | Format-List
