import importlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'web_client'))

import master_control_server
import offline_voice_engine

OPEN = [170, 180, 0, 0, 0, 180]
CLOSE = [40, 0, 180, 180, 180, 0]

class SixServoLatestTests(unittest.TestCase):
    def test_binary_packet_v2(self):
        for mode,payload in [(0x10,[]),(0x01,OPEN),(0x01,CLOSE),(0x02,[55])]:
            pkt = master_control_server.make_packet(mode,payload)
            self.assertEqual(len(pkt),9)
            self.assertEqual(pkt[0],0xAA)
            self.assertEqual(pkt[8],master_control_server.checksum_xor(pkt[:8]))
            self.assertEqual(list(pkt[2:2+len(payload)]),payload)

    def test_voice(self):
        self.assertEqual(offline_voice_engine.OPEN_ANGLE,OPEN)
        self.assertEqual(offline_voice_engine.CLOSED_ANGLE,CLOSE)
        self.assertEqual(offline_voice_engine.GESTURE_PRESETS['fist']['angles'],CLOSE)
        planner=offline_voice_engine.LocalIntentPlanner(offline_voice_engine.VoiceStatus(), lambda s:None)
        self.assertEqual(planner._rule_based_intent('robot disarm')['name'],'DISARM')
        self.assertEqual(planner._rule_based_intent('robot nam tay')['angles'],CLOSE)
        self.assertEqual(planner._rule_based_intent('robot mo ngon ut')['index'],5)

    def test_firmware_config(self):
        uno=(ROOT/'firmware/arduino_uno/robot_hand_uno_realtime_final/Config.cpp').read_text()
        self.assertIn('{2, 3, 4, 5, 8, 7}',uno)
        self.assertIn('{170, 180,   0,   0,   0, 180}',uno)
        self.assertIn('{ 40,   0, 180, 180, 180,   0}',uno)
        esp=(ROOT/'firmware/esp32_ws_bridge/esp32_robot_hand_ws_bridge/BridgeConfig.h').read_text()
        self.assertIn('PACKET_SIZE = 9',esp)

    def test_cv_config(self):
        j=json.loads((ROOT/'pc_client/hand_pose_calibration.json').read_text())
        for k in ('open_ratios','mid_ratios','close_ratios'):
            self.assertEqual(len(j[k]),6)
        p=json.loads((ROOT/'pc_client/servo_tendon_profile.json').read_text())
        self.assertEqual(len(p['profiles']),6)

    def test_browser_endpoints(self):
        for f in ('master_control.html','index.html','realtime_cv_preview.html'):
            html=(ROOT/'web_client'/f).read_text()
            self.assertIn('[170, 180, 0, 0, 0, 180]',html)
            self.assertIn('[40, 0, 180, 180, 180, 0]',html)
            self.assertIn('Uint8Array(9)',html)
            self.assertIn('frame[8]',html)

if __name__ == '__main__':
    unittest.main()
