// TBW-Feeder v3.0 bank controller: 8 lanes, Arduino Nano (ATmega328P), USB serial 115200.
//
// Hardware (see ../../ELECTRONICS.md):
//   servo  lane n -> D2..D9 (signal), 5 V / GND from the Nano IO shield servo rail (external 5 V 4 A).
//          A 13T gear on the servo spline drives a rack on the slider: 1 us = 0.01 mm at the pawl.
//   The cover tape peel is driven mechanically by the same servo stroke (lifter + rack + pinion + one-way
//   bearing), so there is no peel output.
//
// Protocol: one command per line, answer "ok" or "error: <text>" (OpenPnP GcodeDriver defaults).
//   M115                         firmware info
//   M600 N<lane> [F<mm>]         feed F mm (2..24, multiple of 2, default 4); lane 0..7
//   M601 N<lane>                 post-pick hook (no action, answers ok)
//   M603 N<lane> [A<us>] [B<us>] [C<us>] [S<ms>]
//                                set full / half / retract pulse width (500..2500 us, 1 us = 0.01 mm at
//                                the pawl), settle time per move
//   M604 N<lane> S<deg> | U<us>  move the servo to a raw angle or pulse (calibration), position unknown
//   M610 S<0|1>                  S0: release all servos (no holding torque), S1: normal
//   M620                         print the configuration of all lanes
//   M500 / M501 / M502           save to EEPROM / load from EEPROM / factory defaults (not saved)
//
// Feed logic: the pawl has three positions. RETRACT (tooth in the next hole), HALF (tape +2 mm), FULL
// (tape +4 mm). A 2 mm step is RETRACT->HALF or HALF->FULL; from FULL the pawl first goes back to RETRACT
// (no tape motion, the detent holds the tape). The servo keeps holding its last position, so the pick
// pocket stays where the stroke ended. Every feed stroke turns the peel roller 4.8 mm per 4 mm (2.4 mm per
// 2 mm); the sprung nip slips the surplus. v3.0 stores the positions in microseconds: whole degrees were
// 0.11 mm steps at the pawl, too coarse to centre the pocket.

#include <EEPROM.h>
#include <Servo.h>

#define FW_NAME "TBW-Feeder"
#define FW_VERSION "3.0.0"

const uint8_t LANES = 8;
const uint8_t SERVO_PIN[LANES] = {2, 3, 4, 5, 6, 7, 8, 9};

const uint16_t CFG_MAGIC = 0x7B20;
const uint8_t CFG_VERSION = 3;   // 3: positions in microseconds (v3.0)

struct LaneCfg {
  uint16_t full;     // us, pawl at the forward end
  uint16_t half;     // us, pawl 2 mm before the forward end
  uint16_t retract;  // us, pawl 4.2 mm back (tooth in the next hole)
  uint16_t settle;   // ms per servo move
};

struct Config {
  uint16_t magic;
  uint8_t version;
  LaneCfg lane[LANES];
  uint8_t sum;
};

enum Pos : uint8_t { POS_UNKNOWN, POS_RETRACT, POS_HALF, POS_FULL };

Config cfg;
Servo servo[LANES];
Pos pos[LANES];
char line[64];
uint8_t lineLen = 0;

// ------------------------------------------------------------------ configuration
uint8_t checksum(const Config &c) {
  const uint8_t *p = (const uint8_t *)&c;
  uint8_t s = 0x5A;
  for (size_t i = 0; i < sizeof(Config) - 1; i++) s = (uint8_t)(s * 31 + p[i]);
  return s;
}

void defaults() {
  cfg.magic = CFG_MAGIC;
  cfg.version = CFG_VERSION;
  for (uint8_t i = 0; i < LANES; i++) {
    // 13T m1 gear on the spline, rack on the slider, stroke 4.2: forward 108.5, half 90.9, retract 71.5 deg =
    // 1706 / 1510 / 1294 us (500..2500 us = 0..180 deg; mirror around 1500 if the servo turns the other way)
    cfg.lane[i].full = 1706;
    cfg.lane[i].half = 1510;
    cfg.lane[i].retract = 1294;
    cfg.lane[i].settle = 180;
  }
  cfg.sum = checksum(cfg);
}

bool load() {
  Config c;
  EEPROM.get(0, c);
  if (c.magic != CFG_MAGIC || c.version != CFG_VERSION || c.sum != checksum(c)) return false;
  cfg = c;
  return true;
}

void save() {
  cfg.sum = checksum(cfg);
  EEPROM.put(0, cfg);
}

// ------------------------------------------------------------------ motion
const uint16_t US_MIN = 500, US_MAX = 2500;

void moveServo(uint8_t n, uint16_t us) {
  if (!servo[n].attached()) servo[n].attach(SERVO_PIN[n], US_MIN, US_MAX);
  servo[n].writeMicroseconds(us);
  delay(cfg.lane[n].settle);
}

// one 2 mm step; returns the new position
Pos step2(uint8_t n) {
  const LaneCfg &c = cfg.lane[n];
  if (pos[n] == POS_FULL || pos[n] == POS_UNKNOWN) {
    moveServo(n, c.retract);
    pos[n] = POS_RETRACT;
  }
  if (pos[n] == POS_RETRACT) {
    moveServo(n, c.half);
    return POS_HALF;
  }
  moveServo(n, c.full);  // POS_HALF
  return POS_FULL;
}

void feed(uint8_t n, uint8_t mm) {
  for (uint8_t k = 0; k < mm / 2; k++) pos[n] = step2(n);
}

// ------------------------------------------------------------------ command parsing
bool param(const char *s, char key, long &val) {
  for (const char *p = s; *p; p++) {
    if (*p == key && (p == s || p[-1] == ' ')) {
      char *end;
      val = strtol(p + 1, &end, 10);
      return end != p + 1;
    }
  }
  return false;
}

void err(const __FlashStringHelper *msg) {
  Serial.print(F("error: "));
  Serial.println(msg);
}

bool laneArg(const char *s, uint8_t &n) {
  long v;
  if (!param(s, 'N', v) || v < 0 || v >= LANES) {
    err(F("lane N0..N7 required"));
    return false;
  }
  n = (uint8_t)v;
  return true;
}

void printLane(uint8_t n) {
  const LaneCfg &c = cfg.lane[n];
  Serial.print(F("N")); Serial.print(n);
  Serial.print(F(" A")); Serial.print(c.full);
  Serial.print(F(" B")); Serial.print(c.half);
  Serial.print(F(" C")); Serial.print(c.retract);
  Serial.print(F(" S")); Serial.print(c.settle);
  Serial.print(F(" pos ")); Serial.println(pos[n]);
}

void command(char *s) {
  // strip comment, upper-case, skip leading blanks
  for (char *p = s; *p; p++) {
    if (*p == ';' || *p == '(') { *p = 0; break; }
    if (*p >= 'a' && *p <= 'z') *p -= 32;
  }
  while (*s == ' ') s++;
  if (!*s) return;
  long code;
  if (s[0] != 'M' || !param(s, 'M', code)) {
    err(F("unknown command"));
    return;
  }
  uint8_t n;
  long v;
  switch (code) {
    case 115:
      Serial.print(F("FIRMWARE_NAME:" FW_NAME " FIRMWARE_VERSION:" FW_VERSION " LANES:"));
      Serial.println(LANES);
      break;
    case 600: {
      if (!laneArg(s, n)) return;
      long mm = 4;
      param(s, 'F', mm);
      if (mm < 2 || mm > 24 || mm % 2) { err(F("F must be 2..24 and even")); return; }
      feed(n, (uint8_t)mm);
      break;
    }
    case 601:
      if (!laneArg(s, n)) return;
      break;
    case 603: {
      if (!laneArg(s, n)) return;
      LaneCfg c = cfg.lane[n];
      if (param(s, 'A', v)) c.full = (uint16_t)constrain(v, US_MIN, US_MAX);
      if (param(s, 'B', v)) c.half = (uint16_t)constrain(v, US_MIN, US_MAX);
      if (param(s, 'C', v)) c.retract = (uint16_t)constrain(v, US_MIN, US_MAX);
      if (param(s, 'S', v)) c.settle = (uint16_t)constrain(v, 20, 2000);
      cfg.lane[n] = c;
      pos[n] = POS_UNKNOWN;
      printLane(n);
      break;
    }
    case 604:
      if (!laneArg(s, n)) return;
      if (param(s, 'U', v)) {
        if (v < US_MIN || v > US_MAX) { err(F("U500..U2500 required")); return; }
        moveServo(n, (uint16_t)v);
      } else {
        if (!param(s, 'S', v) || v < 0 || v > 180) { err(F("S0..S180 or U500..U2500 required")); return; }
        moveServo(n, (uint16_t)(US_MIN + (v * (long)(US_MAX - US_MIN)) / 180));
      }
      pos[n] = POS_UNKNOWN;
      break;
    case 610:
      if (!param(s, 'S', v)) { err(F("S0 or S1 required")); return; }
      if (v == 0) {             // S1: nothing to do, servos attach again on their next move
        for (uint8_t i = 0; i < LANES; i++) {
          servo[i].detach();
          pos[i] = POS_UNKNOWN;
        }
      }
      break;
    case 620:
      for (uint8_t i = 0; i < LANES; i++) printLane(i);
      break;
    case 500: save(); break;
    case 501:
      if (!load()) { err(F("no valid configuration in EEPROM")); return; }
      for (uint8_t i = 0; i < LANES; i++) pos[i] = POS_UNKNOWN;
      break;
    case 502:
      defaults();
      for (uint8_t i = 0; i < LANES; i++) pos[i] = POS_UNKNOWN;
      break;
    default:
      err(F("unknown command"));
      return;
  }
  Serial.println(F("ok"));
}

// ------------------------------------------------------------------ main
void setup() {
  for (uint8_t i = 0; i < LANES; i++) pos[i] = POS_UNKNOWN;   // servos attach on first use: no jump at power-up
  Serial.begin(115200);
  if (!load()) defaults();
  Serial.println(F("start " FW_NAME " " FW_VERSION));
}

void loop() {
  while (Serial.available()) {
    char ch = (char)Serial.read();
    if (ch == '\r') continue;
    if (ch == '\n') {
      line[lineLen] = 0;
      command(line);
      lineLen = 0;
    } else if (lineLen < sizeof(line) - 1) {
      line[lineLen++] = ch;
    }
  }
}
