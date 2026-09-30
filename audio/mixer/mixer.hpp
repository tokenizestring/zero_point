
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class mixer_c
	{
	public:

		IXAudio2* engine = nullptr;
		IXAudio2MasteringVoice* master = nullptr;
		X3DAUDIO_HANDLE spatial{};
		X3DAUDIO_LISTENER listener{};
		X3DAUDIO_CONE ears{};
		std::vector<structures::sound_clip_s> clips;
		structures::sound_group_s groups[structures::sound_count]{};
		IXAudio2SourceVoice* voices[audio_voices]{};
		std::float_t started[audio_voices]{};
		IXAudio2SourceVoice* ambience[structures::ambience_count]{};
		std::float_t levels[structures::ambience_count]{};
		IXAudio2SourceVoice* fire_voice = nullptr;
		IXAudio2SourceVoice* heart_voice = nullptr;
		IXAudio2SourceVoice* underwater_voice = nullptr;
		IXAudio2SourceVoice* rain_voice = nullptr;
		IXAudio2SourceVoice* gun_voices[audio_gun_voices]{};
		IXAudio2SourceVoice* drones[structures::drone_count]{};
		structures::drone_s drone_states[structures::drone_count]{};
		structures::vec3_s listener_velocity{};
		IXAudio2SubmixVoice* reverb = nullptr;
		IUnknown* reverb_effect = nullptr;
		std::vector<structures::pending_sound_s> pending;
		std::vector<structures::echo_s> echo_cache;
		std::vector<structures::echo_s> echo_candidates;
		structures::vec3_s echo_source{};
		std::float_t echo_time = -100.0f;
		std::float_t acoustic_timer = 0.0f;
		std::uint32_t acoustics = structures::acoustic_count;
		std::uint32_t gun_cursor = 0u;
		structures::vec3_s listener_position{};
		std::float_t fire_level = 0.0f;
		std::float_t heart_level = 0.0f;
		std::float_t underwater_level = 0.0f;
		std::float_t muffle = 1.0f;
		std::float_t shelter = 0.0f;
		std::float_t effects_level = 1.0f;
		std::float_t ambience_level = 1.0f;
		bool roofed = false;
		std::float_t swim_distance = 0.0f;
		std::float_t previous_depth = 0.0f;
		std::float_t clock = 0.0f;
		std::float_t coast = 0.0f;
		std::float_t coast_timer = 0.0f;
		std::float_t step_distance = 0.0f;
		std::uint32_t output_channels = 2u;
		std::uint32_t channel_mask = 0u;
		std::uint32_t seed = 0x6C8E9CF5u;
		bool ready = false;

		bool create();
		void destroy();
		void load_clips();
		void loop(IXAudio2SourceVoice*& voice, std::uint32_t sound, std::uint32_t channels, const XAUDIO2_VOICE_SENDS* sends);
		void drone(std::uint32_t index, structures::vec3_s position, structures::vec3_s velocity, std::float_t loudness, std::float_t pitch, std::float_t reference);
		void blast(std::uint32_t index, std::uint32_t sound);
		void place_drones(std::float_t delta);
		void play(std::uint32_t sound, structures::vec3_s position, std::float_t volume, std::float_t pitch);
		void play_2d(std::uint32_t sound, std::float_t volume, std::float_t pitch);
		void submit(IXAudio2SourceVoice* voice, const structures::sound_clip_s& clip, std::float_t volume, std::float_t pitch);
		void gunshot(structures::vec3_s position, std::uint32_t close_sound, std::uint32_t far_sound, std::float_t loudness, bool local);
		void find_echoes(structures::vec3_s source);
		void bullet(structures::vec3_s origin, structures::vec3_s end, std::uint32_t result);
		std::float_t occlusion(structures::vec3_s source);
		void launch(const structures::pending_sound_s& entry);
		void classify();
		void set_acoustics(std::uint32_t kind);
		std::float_t air_cutoff(std::float_t distance);
		void update(std::float_t delta);
		void footsteps(std::float_t delta);
		void mix_ambience(std::float_t delta);
		std::uint32_t surface_sound(structures::vec3_s position);
		IXAudio2SourceVoice* acquire();
		std::uint32_t pick(std::uint32_t sound);
		std::float_t random();
	};

	extern mixer_c mixer;
}

//=====================================================================================
