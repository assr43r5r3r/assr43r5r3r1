"""
Tests for replay determinism.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.tetris.game import TetrisGame
from src.tetris.replay import (
    ReplayRecorder, ReplayPlayer, ReplayData,
    FrameInput, InputAction
)


class TestReplayRecorder(unittest.TestCase):
    """Test replay recording."""
    
    def test_record_action(self):
        """Test recording actions."""
        recorder = ReplayRecorder(seed=12345, start_level=1)
        
        recorder.record_action(InputAction.MOVE_LEFT)
        recorder.record_action(InputAction.ROTATE_CW)
        recorder.end_frame()
        
        replay = recorder.get_replay()
        
        self.assertEqual(len(replay.inputs), 1)
        self.assertEqual(len(replay.inputs[0].actions), 2)
        self.assertIn(InputAction.MOVE_LEFT, replay.inputs[0].actions)
        self.assertIn(InputAction.ROTATE_CW, replay.inputs[0].actions)
    
    def test_frame_numbers(self):
        """Test frame numbers are correct."""
        recorder = ReplayRecorder(seed=100, start_level=1)
        
        # Frame 0 - action
        recorder.record_action(InputAction.MOVE_LEFT)
        recorder.end_frame()
        
        # Frame 1 - no action
        recorder.end_frame()
        
        # Frame 2 - action
        recorder.record_action(InputAction.HARD_DROP)
        recorder.end_frame()
        
        replay = recorder.get_replay()
        
        self.assertEqual(len(replay.inputs), 2)
        self.assertEqual(replay.inputs[0].frame, 0)
        self.assertEqual(replay.inputs[1].frame, 2)
    
    def test_metadata(self):
        """Test metadata storage."""
        recorder = ReplayRecorder(seed=100, start_level=5)
        recorder.set_metadata("player", "test")
        recorder.set_metadata("score", 1000)
        
        replay = recorder.get_replay()
        
        self.assertEqual(replay.metadata["player"], "test")
        self.assertEqual(replay.metadata["score"], 1000)


class TestReplayPlayer(unittest.TestCase):
    """Test replay playback."""
    
    def test_get_actions(self):
        """Test getting actions from replay."""
        data = ReplayData(
            seed=100,
            start_level=1,
            inputs=[
                FrameInput(frame=0, actions=[InputAction.MOVE_LEFT]),
                FrameInput(frame=5, actions=[InputAction.ROTATE_CW]),
            ]
        )
        
        player = ReplayPlayer(data)
        
        # Frame 0 should have action
        actions = player.get_actions(0)
        self.assertEqual(actions, [InputAction.MOVE_LEFT])
        
        # Frame 1-4 should be empty
        for frame in range(1, 5):
            actions = player.get_actions(frame)
            self.assertEqual(actions, [])
        
        # Frame 5 should have action
        actions = player.get_actions(5)
        self.assertEqual(actions, [InputAction.ROTATE_CW])
    
    def test_advance_frame(self):
        """Test advancing through replay."""
        data = ReplayData(
            seed=100,
            start_level=1,
            inputs=[
                FrameInput(frame=0, actions=[InputAction.MOVE_LEFT]),
                FrameInput(frame=2, actions=[InputAction.ROTATE_CW]),
            ]
        )
        
        player = ReplayPlayer(data)
        
        actions_0 = player.advance_frame()
        self.assertEqual(actions_0, [InputAction.MOVE_LEFT])
        self.assertEqual(player.frame, 1)
        
        actions_1 = player.advance_frame()
        self.assertEqual(actions_1, [])
        
        actions_2 = player.advance_frame()
        self.assertEqual(actions_2, [InputAction.ROTATE_CW])
    
    def test_is_finished(self):
        """Test finished detection."""
        data = ReplayData(
            seed=100,
            start_level=1,
            inputs=[
                FrameInput(frame=0, actions=[InputAction.MOVE_LEFT]),
            ]
        )
        
        player = ReplayPlayer(data)
        
        self.assertFalse(player.is_finished)
        
        player.advance_frame()
        
        self.assertTrue(player.is_finished)


class TestReplaySerialization(unittest.TestCase):
    """Test replay serialization."""
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        data = ReplayData(
            seed=12345,
            start_level=5,
            inputs=[
                FrameInput(frame=0, actions=[InputAction.MOVE_LEFT, InputAction.ROTATE_CW]),
            ],
            metadata={"player": "test"}
        )
        
        d = data.to_dict()
        
        self.assertEqual(d["seed"], 12345)
        self.assertEqual(d["start_level"], 5)
        self.assertEqual(len(d["inputs"]), 1)
        self.assertEqual(d["metadata"]["player"], "test")
    
    def test_from_dict(self):
        """Test restoring from dictionary."""
        d = {
            "seed": 100,
            "start_level": 1,
            "inputs": [
                {"frame": 0, "actions": ["MOVE_LEFT"]},
                {"frame": 5, "actions": ["HARD_DROP"]},
            ],
            "metadata": {}
        }
        
        data = ReplayData.from_dict(d)
        
        self.assertEqual(data.seed, 100)
        self.assertEqual(len(data.inputs), 2)
        self.assertEqual(data.inputs[0].actions[0], InputAction.MOVE_LEFT)
    
    def test_json_roundtrip(self):
        """Test JSON serialization roundtrip."""
        original = ReplayData(
            seed=999,
            start_level=10,
            inputs=[
                FrameInput(frame=0, actions=[InputAction.MOVE_LEFT]),
                FrameInput(frame=10, actions=[InputAction.HARD_DROP]),
            ],
            metadata={"version": "1.0"}
        )
        
        json_str = original.to_json()
        restored = ReplayData.from_json(json_str)
        
        self.assertEqual(restored.seed, original.seed)
        self.assertEqual(restored.start_level, original.start_level)
        self.assertEqual(len(restored.inputs), len(original.inputs))
        self.assertEqual(
            restored.inputs[0].actions,
            original.inputs[0].actions
        )


class TestGameDeterminism(unittest.TestCase):
    """Test that games are deterministic with same seed and inputs."""
    
    def test_same_seed_same_pieces(self):
        """Test same seed produces same piece sequence."""
        game1 = TetrisGame(seed=12345)
        game2 = TetrisGame(seed=12345)
        
        pieces1 = [game1.current_piece.piece_type]
        pieces2 = [game2.current_piece.piece_type]
        
        for _ in range(10):
            game1.hard_drop()
            game2.hard_drop()
            
            if game1.current_piece and game2.current_piece:
                pieces1.append(game1.current_piece.piece_type)
                pieces2.append(game2.current_piece.piece_type)
        
        self.assertEqual(pieces1, pieces2)
    
    def test_same_inputs_same_result(self):
        """Test same inputs produce same game state."""
        seed = 54321
        
        # Play game 1
        game1 = TetrisGame(seed=seed)
        game1.move_left()
        game1.move_left()
        game1.rotate_cw()
        game1.hard_drop()
        
        # Play game 2 with same inputs
        game2 = TetrisGame(seed=seed)
        game2.move_left()
        game2.move_left()
        game2.rotate_cw()
        game2.hard_drop()
        
        # Should have same score and board state
        self.assertEqual(game1.score, game2.score)
        
        # Board states should match
        grid1 = game1.board.get_state()
        grid2 = game2.board.get_state()
        self.assertEqual(grid1, grid2)


if __name__ == "__main__":
    unittest.main()
