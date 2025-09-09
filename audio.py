import pygame
import os
import threading
import time
from resources import load_sound, resource_path
from constants import DEFAULT_SFX_VOLUME, DEFAULT_MUSIC_VOLUME, DEBUG


class AudioManager:
    def __init__(self):
        # pygame.mixer が初期化されていなければ初期化を試みる
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except Exception:
            # 初期化に失敗しても他処理は継続できるようにする
            pass

        # キャッシュ: name -> Sound or None
        self._sfx_cache = {}
        # 初期音量は constants.py のデフォルトを使用
        self.music_volume = DEFAULT_MUSIC_VOLUME
        self.sfx_volume = DEFAULT_SFX_VOLUME
        self.muted = False

    def load(self, name, sounds_dir=None):
        """resources.load_sound を使ってロードしキャッシュする"""
        try:
            if name in self._sfx_cache:
                return self._sfx_cache[name]
            snd = load_sound(name, sounds_dir=sounds_dir)
            self._sfx_cache[name] = snd
            return snd
        except Exception as e:
            self._sfx_cache[name] = None
            return None

    def play_sound(self, name, volume=None, duration=None, fade_in=0.0, fade_out=0.0):
        """効果音を再生。オプション:
        - duration: 再生全体の秒数 (float)。指定すると duration 秒後に stop または fade_out を実行。
        - fade_in: フェードイン秒 (float)
        - fade_out: フェードアウト秒 (float)
        例: play_sound('heal', duration=1.0, fade_out=0.5)
        """
        try:
            # Ensure mixer is initialized (some imports may occur before pygame.init())
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
            except Exception:
                # if init fails, continue and attempts to load/play will likely no-op
                pass

            if self.muted:
                return

            snd = self._sfx_cache.get(name)
            if snd is None and name not in self._sfx_cache:
                if DEBUG:
                    print(f"[DEBUG] play_sound('{name}'): not in cache, attempting load")
                snd = self.load(name)
            if not snd:
                return

            # effective volume: global sfx_volume * per-call volume (if specified)
            eff_vol = self.sfx_volume if volume is None else (self.sfx_volume * float(volume))
            try:
                eff_vol = max(0.0, min(1.0, eff_vol))
            except Exception:
                eff_vol = self.sfx_volume

            try:
                # set sample volume
                snd.set_volume(eff_vol)
            except Exception as e:
                if DEBUG:
                    print(f"[DEBUG] play_sound('{name}'): set_volume failed: {e}")

            # proceed to play

            # convert seconds to milliseconds for pygame API
            fade_in_ms = int(max(0.0, float(fade_in)) * 1000)

            # play and get Channel
            try:
                ch = snd.play(fade_ms=fade_in_ms)
            except Exception:
                ch = None

            # schedule fadeout/stop if duration is provided
            if duration is not None:
                try:
                    d = float(duration)
                except Exception:
                    d = None
                if d is not None:
                    # calculate when to start fadeout
                    fo = max(0.0, float(fade_out))
                    wait_before_fade = max(0.0, d - fo)

                    def _fade_worker(channel, wait, fade_ms):
                        try:
                            time.sleep(wait)
                            if channel is None:
                                return
                            # fade_ms == 0 => immediate stop
                            if fade_ms > 0:
                                try:
                                    channel.fadeout(fade_ms)
                                except Exception:
                                    try:
                                        channel.stop()
                                    except Exception:
                                        pass
                            else:
                                try:
                                    channel.stop()
                                except Exception:
                                    pass
                        except Exception:
                            pass

                    fade_ms = int(fo * 1000)
                    t = threading.Thread(target=_fade_worker, args=(ch, wait_before_fade, fade_ms), daemon=True)
                    t.start()

            return
        except Exception:
            pass

    def play_music(self, name, loops=-1, fade_ms=0, volume=None):
        try:
            if self.muted:
                return
            path = resource_path(os.path.join('assets', 'sfx', name))
            # try common extensions
            for ext in ('.ogg', '.mp3', '.wav'):
                p = path + ext
                if os.path.exists(p):
                    try:
                        pygame.mixer.music.load(p)
                        vol = self.music_volume if volume is None else volume
                        pygame.mixer.music.set_volume(max(0.0, min(1.0, vol)))
                        pygame.mixer.music.play(loops=loops, fade_ms=fade_ms)
                    except Exception as e:
                        pass
                    return
        except Exception:
            pass

    def stop_music(self, fade_ms=0):
        try:
            if fade_ms > 0:
                try:
                    pygame.mixer.music.fadeout(fade_ms)
                except Exception:
                    pygame.mixer.music.stop()
            else:
                pygame.mixer.music.stop()
        except Exception:
            pass

    def set_sfx_volume(self, v):
        try:
            self.sfx_volume = max(0.0, min(1.0, v))
        except Exception:
            pass

    def set_music_volume(self, v):
        try:
            self.music_volume = max(0.0, min(1.0, v))
            pygame.mixer.music.set_volume(self.music_volume)
        except Exception:
            pass

    def mute(self, m=True):
        self.muted = bool(m)


# グローバルインスタンス
audio = AudioManager()

__all__ = ['audio', 'AudioManager']
