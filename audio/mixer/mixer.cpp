
//=====================================================================================

#include "../../stdafx.hpp"

//=====================================================================================

namespace zp
{
	mixer_c mixer;

	bool mixer_c::create()
	{
		if (SUCCEEDED(XAudio2Create(&engine, 0u, XAUDIO2_DEFAULT_PROCESSOR)) && SUCCEEDED(engine->CreateMasteringVoice(&master)))
		{
			XAUDIO2_VOICE_DETAILS details{};
			DWORD mask{ 0u };

			master->GetVoiceDetails(&details);
			master->GetChannelMask(&mask);
			master->SetVolume(audio_master_volume);

			output_channels = std::clamp(details.InputChannels, 1u, 8u);
			channel_mask = mask;

			if (SUCCEEDED(X3DAudioInitialize(channel_mask, X3DAUDIO_SPEED_OF_SOUND, spatial)))
			{
				const WAVEFORMATEX mono{ WAVE_FORMAT_PCM, 1u, 44100u, 88200u, 2u, 16u, 0u };

				ears = { X3DAUDIO_PI * 1.15f, X3DAUDIO_2PI * 0.94f, 1.0f, audio_rear_volume, 0.0f, audio_rear_muffle, 1.0f, 1.0f };
				listener.pCone = &ears;

				load_clips();

				if (SUCCEEDED(XAudio2CreateReverb(&reverb_effect, 0u)))
				{
					XAUDIO2_EFFECT_DESCRIPTOR descriptor{ reverb_effect, TRUE, 2u };

					const XAUDIO2_EFFECT_CHAIN chain{ 1u, &descriptor };

					if (SUCCEEDED(engine->CreateSubmixVoice(&reverb, 2u, details.InputSampleRate, 0u, 0u, nullptr, &chain)))
					{
						reverb->SetVolume(audio_reverb_volume);

						set_acoustics(structures::acoustic_plain);
					}
				}

				XAUDIO2_SEND_DESCRIPTOR sends[2] = { { 0u, master }, { 0u, reverb } };

				const XAUDIO2_VOICE_SENDS list{ reverb ? 2u : 1u, sends };

				for (auto& voice : voices)
				{
					engine->CreateSourceVoice(&voice, &mono, XAUDIO2_VOICE_USEFILTER, 4.0f, nullptr, &list);
				}

				for (auto& voice : gun_voices)
				{
					engine->CreateSourceVoice(&voice, &mono, XAUDIO2_VOICE_USEFILTER, 4.0f, nullptr, &list);
				}

				const WAVEFORMATEX stereo{ WAVE_FORMAT_PCM, 2u, 44100u, 176400u, 4u, 16u, 0u };

				XAUDIO2_SEND_DESCRIPTOR dry{ 0u, master };

				const XAUDIO2_VOICE_SENDS direct{ 1u, &dry };

				for (auto& voice : tail_voices)
				{
					engine->CreateSourceVoice(&voice, &stereo, XAUDIO2_VOICE_USEFILTER, 4.0f, nullptr, &direct);
				}

				loop(ring_voice, structures::sound_tinnitus, 1u, nullptr);

				for (auto index{ 0u }; index < structures::ambience_count; index++)
				{
					loop(ambience[index], ambience_sounds[index], 2u, nullptr);
				}

				loop(fire_voice, structures::sound_fire, 1u, nullptr);
				loop(heart_voice, structures::sound_heartbeat, 1u, nullptr);
				loop(underwater_voice, structures::sound_underwater, 1u, nullptr);
				loop(rain_voice, structures::sound_amb_rain, 2u, nullptr);

				for (auto index{ 0u }; index < structures::drone_count; index++)
				{
					drone_states[index] = {};
					drone_states[index].queued = structures::sound_count;

					if (drone_sounds[index] < structures::sound_count)
					{
						loop(drones[index], drone_sounds[index], 1u, &list);
					}

					else
					{
						engine->CreateSourceVoice(&drones[index], &mono, XAUDIO2_VOICE_USEFILTER, 4.0f, nullptr, &list);
					}
				}

				ready = std::all_of(std::begin(voices), std::end(voices), [](IXAudio2SourceVoice* voice) { return voice != nullptr; });
			}
		}

		logger.write("mixer: %s, %u output channels, %zu clips, reverb %s", ready ? "ready" : "unavailable", output_channels, clips.size(), gun_voices[0] ? "on" : "off");

		return ready;
	}
	/*
	//=====================================================================================
	*/
	void mixer_c::destroy()
	{
		for (auto& voice : voices)
		{
			if (voice)
			{
				voice->DestroyVoice();

				voice = nullptr;
			}
		}

		for (auto& voice : ambience)
		{
			if (voice)
			{
				voice->DestroyVoice();

				voice = nullptr;
			}
		}

		if (fire_voice)
		{
			fire_voice->DestroyVoice();

			fire_voice = nullptr;
		}

		if (heart_voice)
		{
			heart_voice->DestroyVoice();

			heart_voice = nullptr;
		}

		if (underwater_voice)
		{
			underwater_voice->DestroyVoice();

			underwater_voice = nullptr;
		}

		if (rain_voice)
		{
			rain_voice->DestroyVoice();

			rain_voice = nullptr;
		}

		for (auto& voice : gun_voices)
		{
			if (voice)
			{
				voice->DestroyVoice();

				voice = nullptr;
			}
		}

		for (auto& voice : tail_voices)
		{
			if (voice)
			{
				voice->DestroyVoice();

				voice = nullptr;
			}
		}

		if (ring_voice)
		{
			ring_voice->DestroyVoice();

			ring_voice = nullptr;
		}

		for (auto& voice : drones)
		{
			if (voice)
			{
				voice->DestroyVoice();

				voice = nullptr;
			}
		}

		if (reverb)
		{
			reverb->DestroyVoice();

			reverb = nullptr;
		}

		functions::release(reverb_effect);

		pending.clear();

		if (master)
		{
			master->DestroyVoice();

			master = nullptr;
		}

		functions::release(engine);

		clips.clear();

		ready = false;
	}
	/*
	//=====================================================================================
	*/
	void mixer_c::load_clips()
	{
		char name[pak_name_length]{};

		clips.clear();

		for (auto sound{ 0u }; sound < structures::sound_count; sound++)
		{
			groups[sound].first = static_cast<std::uint32_t>(clips.size());

			for (auto variant{ 0u }; variant < 32u; variant++)
			{
				std::snprintf(name, sizeof(name), "sound_%s_%u", sound_names[sound], variant);

				for (auto index{ 0u }; pak.entries && index < pak.header->entry_count; index++)
				{
					if (const auto& entry{ pak.entries[index] }; entry.type == structures::pak_type_sound && std::strcmp(entry.name, name) == 0)
					{
						clips.push_back({ pak.data(&entry), static_cast<std::uint32_t>(entry.size), entry.height, entry.format, entry.width });
					}
				}
			}

			std::snprintf(name, sizeof(name), "sound_%s", sound_names[sound]);

			for (auto index{ 0u }; pak.entries && index < pak.header->entry_count && clips.size() == groups[sound].first; index++)
			{
				if (const auto& entry{ pak.entries[index] }; entry.type == structures::pak_type_sound && std::strcmp(entry.name, name) == 0)
				{
					clips.push_back({ pak.data(&entry), static_cast<std::uint32_t>(entry.size), entry.height, entry.format, entry.width });
				}
			}

			groups[sound].count = static_cast<std::uint32_t>(clips.size()) - groups[sound].first;
		}
	}
	/*
	//=====================================================================================
	*/
	void mixer_c::loop(IXAudio2SourceVoice*& voice, std::uint32_t sound, std::uint32_t channels, const XAUDIO2_VOICE_SENDS* sends)
	{
		const WAVEFORMATEX format{ WAVE_FORMAT_PCM, static_cast<WORD>(channels), 44100u, 44100u * 2u * channels, static_cast<WORD>(2u * channels), 16u, 0u };

		if (groups[sound].count && clips[groups[sound].first].channels == channels && SUCCEEDED(engine->CreateSourceVoice(&voice, &format, XAUDIO2_VOICE_USEFILTER, 4.0f, nullptr, sends)))
		{
			const auto& clip{ clips[groups[sound].first] };

			XAUDIO2_BUFFER buffer{};

			buffer.AudioBytes = clip.bytes;
			buffer.pAudioData = clip.data;
			buffer.LoopCount = XAUDIO2_LOOP_INFINITE;

			voice->SubmitSourceBuffer(&buffer);
			voice->SetVolume(0.0f);
			voice->Start();
		}
	}
	/*
	//=====================================================================================
	*/
	void mixer_c::play(std::uint32_t sound, structures::vec3_s position, std::float_t volume, std::float_t pitch)
	{
		if (ready && sound < structures::sound_count && groups[sound].count && mathematics.distance(position, listener_position) < audio_audible_range)
		{
			if (const auto& clip{ clips[pick(sound)] }; clip.channels == 1u)
			{
				if (const auto voice{ acquire() }; voice)
				{
					std::float_t matrix[8]{};

					X3DAUDIO_EMITTER emitter{};
					X3DAUDIO_DSP_SETTINGS settings{};

					emitter.Position = { position.x, position.y, position.z };
					emitter.OrientFront = { 0.0f, 0.0f, 1.0f };
					emitter.OrientTop = { 0.0f, 1.0f, 0.0f };
					emitter.ChannelCount = 1u;
					emitter.CurveDistanceScaler = audio_rolloff;
					emitter.DopplerScaler = 0.0f;

					settings.SrcChannelCount = 1u;
					settings.DstChannelCount = output_channels;
					settings.pMatrixCoefficients = matrix;

					X3DAudioCalculate(spatial, &listener, &emitter, X3DAUDIO_CALCULATE_MATRIX | X3DAUDIO_CALCULATE_LPF_DIRECT, &settings);

					const auto blocked{ occlusion(position) };
					const XAUDIO2_FILTER_PARAMETERS filter{ LowPassFilter, std::min(2.0f * std::sin(pi / 6.0f * settings.LPFDirectCoefficient) * mathematics.lerp(1.0f, audio_occlusion_muffle, blocked), muffle), 1.0f };
					const std::float_t send[2] = { audio_spatial_send, audio_spatial_send };

					voice->SetOutputMatrix(master, 1u, output_channels, matrix);
					voice->SetFilterParameters(&filter);

					if (reverb)
					{
						voice->SetOutputMatrix(reverb, 1u, 2u, send);
					}

					submit(voice, clip, volume * (1.0f - blocked * audio_occlusion_loss), pitch);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void mixer_c::play_2d(std::uint32_t sound, std::float_t volume, std::float_t pitch)
	{
		if (ready && sound < structures::sound_count && groups[sound].count)
		{
			if (const auto& clip{ clips[pick(sound)] }; clip.channels == 1u)
			{
				if (const auto voice{ acquire() }; voice)
				{
					std::float_t matrix[8]{};

					const XAUDIO2_FILTER_PARAMETERS filter{ LowPassFilter, muffle, 1.0f };
					const std::float_t dry[2] = { 0.0f, 0.0f };

					matrix[0] = output_channels > 1u ? 0.707f : 1.0f;
					matrix[1] = output_channels > 1u ? 0.707f : 0.0f;

					voice->SetOutputMatrix(master, 1u, output_channels, matrix);
					voice->SetFilterParameters(&filter);

					if (reverb)
					{
						voice->SetOutputMatrix(reverb, 1u, 2u, dry);
					}

					submit(voice, clip, volume, pitch);
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void mixer_c::submit(IXAudio2SourceVoice* voice, const structures::sound_clip_s& clip, std::float_t volume, std::float_t pitch)
	{
		XAUDIO2_BUFFER buffer{};

		buffer.AudioBytes = clip.bytes;
		buffer.pAudioData = clip.data;
		buffer.Flags = XAUDIO2_END_OF_STREAM;

		voice->Stop();
		voice->FlushSourceBuffers();
		voice->SubmitSourceBuffer(&buffer);
		voice->SetVolume(volume * effects_level);
		voice->SetFrequencyRatio(std::clamp(pitch, 0.25f, 3.9f));
		voice->Start();
	}
	/*
	//=====================================================================================
	*/
	void mixer_c::gunshot(structures::vec3_s position, std::uint32_t weapon, bool local)
	{
		const auto kind{ std::min(weapon, static_cast<std::uint32_t>(structures::weapon_count) - 1u) };
		const auto& layers{ gun_sounds[kind] };
		const auto loudness{ weapon_definitions[kind].loudness };
		const auto distance{ local ? 0.0f : mathematics.distance(position, listener_position) };

		if (ready && gun_voices[0] && layers.close < structures::sound_count && distance < audio_gun_range * loudness)
		{
			const auto delay{ distance / audio_speed_of_sound };
			const auto blocked{ local ? 0.0f : occlusion(position) };
			const auto level{ loudness * std::pow(audio_gun_reference / (audio_gun_reference + distance), 0.75f) * (1.0f - blocked * audio_occlusion_loss) };
			const auto close_weight{ std::clamp(1.0f - (distance - 25.0f) / 230.0f, 0.0f, 1.0f) * (1.0f - blocked * 0.6f) };
			const auto far_weight{ local ? 0.0f : std::clamp((distance - 30.0f) / 170.0f, 0.0f, 1.0f) };
			const auto cutoff{ air_cutoff(distance) * mathematics.lerp(1.0f, audio_occlusion_muffle, blocked) };
			const auto pitch{ 0.97f + random() * 0.06f };
			const auto room{ local ? acoustics : surroundings(position) };
			const auto space{ room < structures::acoustic_count ? audio_tail_gains[room] : 0.0f };
			const auto tail_level{ loudness * space * std::pow(audio_tail_reference / (audio_tail_reference + distance), 0.6f) * (1.0f - blocked * 0.3f) };
			const auto side{ local ? mathematics.right_from_yaw(player.yaw) : mathematics.flat_forward(random() * two_pi) };

			if (close_weight > 0.0f)
			{
				pending.push_back({ clock + delay, layers.close, position, std::min(1.0f, level * close_weight), pitch, cutoff, audio_reverb_send * (local ? 0.5f : 1.0f), local == false });
			}

			if (far_weight > 0.0f)
			{
				pending.push_back({ clock + delay, layers.distant, position, std::min(1.0f, level * far_weight * 1.4f), pitch, cutoff, audio_reverb_send * (1.5f + blocked), true });
			}

			if (local || distance < audio_mechanism_range)
			{
				pending.push_back({ clock + delay, layers.mechanism, position, local ? 0.5f : 0.4f * (1.0f - distance / audio_mechanism_range), 0.98f + random() * 0.04f, 16000.0f, 0.0f, local == false });
			}

			if (tail_level > 0.005f && room < structures::acoustic_underwater)
			{
				pending.push_back({ clock + delay + 0.004f, layers.tail + room, position, std::min(1.0f, tail_level), pitch, air_cutoff(distance * 0.6f) * mathematics.lerp(1.0f, 0.6f, blocked), 0.0f, false });
			}

			find_echoes(position);

			for (const auto& echo : echo_cache)
			{
				pending.push_back({ clock + echo.path / audio_speed_of_sound, layers.distant, echo.position, std::min(1.0f, loudness * echo.strength * std::pow(audio_gun_reference / (audio_gun_reference + echo.path), 0.6f) * 2.2f), pitch * 0.97f, air_cutoff(echo.path) * 0.6f, audio_reverb_send * 2.0f, true });
			}

			if (layers.ejects)
			{
				casing(position, side, local);
			}

			deafen((local ? 1.0f : mathematics.saturate(1.0f - distance / audio_deafen_range)) * layers.deafening * (room == structures::acoustic_room ? audio_room_deafening : 1.0f));
		}
	}
	/*
	//=====================================================================================
	*/
	void mixer_c::casing(structures::vec3_s position, structures::vec3_s side, bool local)
	{
		const auto spot{ position + side * (0.55f + random() * 0.5f) };
		const auto ground{ world.trace(spot, spot - structures::vec3_s{ 0.0f, 3.0f, 0.0f }, {}, structures::contents_solid) };
		const auto landing{ ground.hit ? ground.end : spot - structures::vec3_s{ 0.0f, 1.6f, 0.0f } };
		const auto step{ surface_sound(landing) };
		const auto sound{ step == structures::sound_step_wood ? structures::sound_casing_wood : (step == structures::sound_step_concrete || step == structures::sound_step_gravel ? structures::sound_casing_hard : structures::sound_casing_soft) };
		const auto distance{ mathematics.distance(landing, listener_position) };

		if (ready && distance < audio_casing_range)
		{
			pending.push_back({ clock + audio_casing_delay + random() * 0.15f + distance / audio_speed_of_sound, sound, landing, (local ? 0.42f : 0.5f) * (1.0f - distance / audio_casing_range), 0.9f + random() * 0.25f, 16000.0f, audio_reverb_send * 0.5f, true });
		}
	}
	/*
	//=====================================================================================
	*/
	void mixer_c::deafen(std::float_t amount)
	{
		if (menu.user.ear_ringing && amount > 0.0f)
		{
			deafness = std::min(deafness + amount, 1.0f);
		}
	}
	/*
	//=====================================================================================
	*/
	void mixer_c::find_echoes(structures::vec3_s source)
	{
		if (clock - echo_time > audio_echo_cache || mathematics.distance(source, echo_source) > 1.5f)
		{
			echo_cache.clear();
			echo_candidates.clear();

			echo_source = source;
			echo_time = clock;

			for (auto ray{ 0u }; ray < audio_echo_rays; ray++)
			{
				const auto yaw{ two_pi * (static_cast<std::float_t>(ray) + random()) / static_cast<std::float_t>(audio_echo_rays) };
				const structures::vec3_s heading{ std::sin(yaw), 0.0f, std::cos(yaw) };
				const auto start{ source + structures::vec3_s{ 0.0f, 1.2f, 0.0f } };
				const auto wall{ world.trace(start, start + heading * audio_echo_wall_reach, {}, structures::contents_solid) };

				if (wall.fraction < 1.0f && wall.surface != structures::surface_wood && wall.fraction * audio_echo_wall_reach > 4.0f)
				{
					echo_candidates.push_back({ wall.end, wall.fraction * audio_echo_wall_reach + mathematics.distance(wall.end, listener_position), std::fabs(mathematics.dot(wall.normal, heading)) * 0.9f + 0.1f });
				}

				else if (terrain.enabled)
				{
					auto found{ false };

					for (auto step{ audio_echo_step * 7.0f }; found == false && step < audio_echo_reach; step += audio_echo_step)
					{
						const auto probe{ start + heading * step };
						const auto ceiling{ probe.y + step * 0.04f };
						const auto ground{ terrain.height(probe.x, probe.z) };

						if (ground > ceiling)
						{
							const structures::vec3_s point{ probe.x, std::min(ground, ceiling + 6.0f), probe.z };

							echo_candidates.push_back({ point, step + mathematics.distance(point, listener_position), std::clamp((ground - ceiling) / 12.0f, 0.25f, 1.0f) });

							found = true;
						}
					}
				}
			}

			std::sort(echo_candidates.begin(), echo_candidates.end(), [](const structures::echo_s& a, const structures::echo_s& b) { return a.strength / a.path > b.strength / b.path; });

			for (auto index{ 0u }; index < echo_candidates.size() && index < audio_echo_count; index++)
			{
				echo_cache.push_back(echo_candidates[index]);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void mixer_c::bullet(structures::vec3_s origin, structures::vec3_s end, std::uint32_t result)
	{
		const auto path{ end - origin };
		const auto length{ mathematics.length(path) };

		if (ready && gun_voices[0] && length > 1.0f)
		{
			const auto direction{ path / length };
			const auto along{ std::clamp(mathematics.dot(listener_position - origin, direction), 0.0f, length) };
			const auto closest{ origin + direction * along };
			const auto miss{ mathematics.distance(closest, listener_position) };
			const auto flight{ along / audio_bullet_speed };
			const auto landing{ mathematics.distance(end, listener_position) };
			const auto surface{ result == 255u ? static_cast<std::uint32_t>(structures::surface_flesh) : result };

			if (miss < audio_crack_radius && along > audio_crack_minimum && along < length - 0.5f)
			{
				const auto strength{ mathematics.saturate(1.0f - miss / audio_crack_radius) };

				pending.push_back({ clock + flight + miss / audio_speed_of_sound, structures::sound_bullet_crack, closest, 0.3f + 0.7f * strength, 0.92f + random() * 0.16f, 16000.0f, audio_reverb_send * 1.3f, true });

				if (miss < audio_whiz_radius)
				{
					pending.push_back({ clock + std::max(flight - 0.15f, 0.0f), structures::sound_bullet_whiz, closest, 0.5f + 0.5f * mathematics.saturate(1.0f - miss / audio_whiz_radius), 0.9f + random() * 0.2f, 12000.0f, audio_reverb_send * 0.5f, true });
				}
			}

			if (surface < structures::surface_count && landing < audio_impact_range)
			{
				const auto arrival{ clock + length / audio_bullet_speed + landing / audio_speed_of_sound };
				const auto level{ 0.35f + 0.6f * mathematics.saturate(1.0f - landing / audio_impact_range) };

				pending.push_back({ arrival, impact_sounds[surface], end, level, 0.9f + random() * 0.2f, air_cutoff(landing), audio_reverb_send, true });

				if (ricochet_surfaces[surface] && random() < 0.35f)
				{
					pending.push_back({ arrival + 0.01f, structures::sound_ricochet, end, level * 0.8f, 0.9f + random() * 0.25f, air_cutoff(landing), audio_reverb_send * 1.4f, true });
				}
			}
		}
	}
	/*
	//=====================================================================================
	*/
	std::float_t mixer_c::occlusion(structures::vec3_s source)
	{
		const auto offset{ source - listener_position };
		const auto distance{ mathematics.length(offset) };
		const auto samples{ std::clamp(static_cast<std::uint32_t>(distance / 6.0f), 4u, audio_occlusion_samples) };

		auto blocked{ 0.0f };

		if (distance > 1.5f)
		{
			const auto toward{ offset / distance };
			const auto reach{ std::min(distance, audio_occlusion_reach) };
			const auto tail{ std::min(reach, distance - reach) };
			const auto near_wall{ world.trace(listener_position, listener_position + toward * reach, {}, structures::contents_solid).fraction < (distance > reach ? 1.0f : 0.97f) };
			const auto far_wall{ tail > 1.0f && world.trace(source - toward * tail, source, {}, structures::contents_solid).fraction < 0.97f };

			blocked = near_wall || far_wall ? audio_occlusion_wall : 0.0f;

			for (auto sample{ 1u }; terrain.enabled && sample < samples; sample++)
			{
				const auto fraction{ static_cast<std::float_t>(sample) / static_cast<std::float_t>(samples) };
				const auto point{ listener_position + offset * fraction + structures::vec3_s{ 0.0f, 0.6f * fraction, 0.0f } };

				blocked = std::max(blocked, mathematics.saturate((terrain.height(point.x, point.z) - point.y) / 3.0f));
			}
		}

		return blocked;
	}
	/*
	//=====================================================================================
	*/
	void mixer_c::launch(const structures::pending_sound_s& entry)
	{
		if (entry.sound < structures::sound_count && groups[entry.sound].count)
		{
			if (const auto& clip{ clips[pick(entry.sound)] }; clip.channels == 2u)
			{
				if (const auto voice{ tail_voices[tail_cursor] }; voice)
				{
					std::float_t matrix[16]{};

					const XAUDIO2_FILTER_PARAMETERS filter{ LowPassFilter, std::min(2.0f * std::sin(pi * std::min(entry.cutoff, 7350.0f) / 44100.0f), muffle), 1.0f };

					matrix[0] = output_channels > 1u ? 1.0f : 0.5f;
					matrix[1] = output_channels > 1u ? 0.0f : 0.5f;
					matrix[3] = output_channels > 1u ? 1.0f : 0.0f;
					matrix[8] = output_channels >= 6u ? 0.45f : 0.0f;
					matrix[11] = output_channels >= 6u ? 0.45f : 0.0f;

					voice->SetOutputMatrix(master, 2u, output_channels, matrix);
					voice->SetFilterParameters(&filter);

					submit(voice, clip, entry.volume, entry.pitch);
				}

				tail_cursor = (tail_cursor + 1u) % audio_tail_voices;
			}

			else if (clip.channels == 1u)
			{
				if (const auto voice{ gun_voices[gun_cursor] }; voice)
				{
					std::float_t matrix[8]{};

					const std::float_t send[2] = { entry.send, entry.send };

					auto shadow{ 1.0f };

					if (entry.spatial)
					{
						X3DAUDIO_EMITTER emitter{};
						X3DAUDIO_DSP_SETTINGS settings{};

						emitter.Position = { entry.position.x, entry.position.y, entry.position.z };
						emitter.OrientFront = { 0.0f, 0.0f, 1.0f };
						emitter.OrientTop = { 0.0f, 1.0f, 0.0f };
						emitter.ChannelCount = 1u;
						emitter.CurveDistanceScaler = audio_gun_range * 10.0f;
						emitter.DopplerScaler = 0.0f;

						settings.SrcChannelCount = 1u;
						settings.DstChannelCount = output_channels;
						settings.pMatrixCoefficients = matrix;

						X3DAudioCalculate(spatial, &listener, &emitter, X3DAUDIO_CALCULATE_MATRIX | X3DAUDIO_CALCULATE_LPF_DIRECT, &settings);

						shadow = std::sin(pi / 6.0f * settings.LPFDirectCoefficient) * 2.0f;
					}

					else
					{
						matrix[0] = output_channels > 1u ? 0.707f : 1.0f;
						matrix[1] = output_channels > 1u ? 0.707f : 0.0f;
					}

					const XAUDIO2_FILTER_PARAMETERS filter{ LowPassFilter, std::min(2.0f * std::sin(pi * std::min(entry.cutoff, 7350.0f) / 44100.0f) * shadow, muffle), 1.0f };

					voice->SetOutputMatrix(master, 1u, output_channels, matrix);
					voice->SetFilterParameters(&filter);

					if (reverb)
					{
						voice->SetOutputMatrix(reverb, 1u, 2u, send);
					}

					submit(voice, clip, entry.volume, entry.pitch);
				}

				gun_cursor = (gun_cursor + 1u) % audio_gun_voices;
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void mixer_c::drone(std::uint32_t index, structures::vec3_s position, structures::vec3_s velocity, std::float_t loudness, std::float_t pitch, std::float_t reference)
	{
		if (index < structures::drone_count)
		{
			auto& state{ drone_states[index] };

			state.position = position;
			state.velocity = velocity;
			state.loudness = loudness;
			state.pitch = pitch;
			state.reference = reference;
			state.fresh = true;
		}
	}
	/*
	//=====================================================================================
	*/
	void mixer_c::blast(std::uint32_t index, std::uint32_t sound)
	{
		if (ready && index < structures::drone_count && sound < structures::sound_count && groups[sound].count)
		{
			drone_states[index].queued = sound;
			drone_states[index].delay = mathematics.distance(drone_states[index].position, listener_position) / audio_speed_of_sound;
		}
	}
	/*
	//=====================================================================================
	*/
	void mixer_c::place_drones(std::float_t delta)
	{
		for (auto index{ 0u }; index < structures::drone_count; index++)
		{
			auto& state{ drone_states[index] };

			if (const auto voice{ drones[index] }; voice)
			{
				XAUDIO2_VOICE_STATE playing{};

				const auto distance{ mathematics.distance(state.position, listener_position) };
				const auto level{ state.fresh && distance < audio_drone_range ? state.loudness * state.reference / (state.reference + distance) : 0.0f };

				state.delay -= delta;

				if (state.queued < structures::sound_count && state.delay <= 0.0f)
				{
					submit(voice, clips[pick(state.queued)], 0.0f, state.pitch);

					state.queued = structures::sound_count;
				}

				voice->GetState(&playing, XAUDIO2_VOICE_NOSAMPLESPLAYED);

				if (level > audio_drone_floor && playing.BuffersQueued)
				{
					std::float_t matrix[8]{};

					X3DAUDIO_EMITTER emitter{};
					X3DAUDIO_DSP_SETTINGS settings{};

					emitter.Position = { state.position.x, state.position.y, state.position.z };
					emitter.Velocity = { state.velocity.x, state.velocity.y, state.velocity.z };
					emitter.OrientFront = { 0.0f, 0.0f, 1.0f };
					emitter.OrientTop = { 0.0f, 1.0f, 0.0f };
					emitter.ChannelCount = 1u;
					emitter.CurveDistanceScaler = audio_drone_range * 10.0f;
					emitter.DopplerScaler = 1.0f;

					settings.SrcChannelCount = 1u;
					settings.DstChannelCount = output_channels;
					settings.pMatrixCoefficients = matrix;

					X3DAudioCalculate(spatial, &listener, &emitter, X3DAUDIO_CALCULATE_MATRIX | X3DAUDIO_CALCULATE_LPF_DIRECT | X3DAUDIO_CALCULATE_DOPPLER, &settings);

					state.recheck -= delta;

					if (state.recheck <= 0.0f)
					{
						state.blocked = occlusion(state.position);
						state.recheck = audio_drone_recheck * (1.0f + 0.25f * static_cast<std::float_t>(index));
					}

					const auto blocked{ state.blocked };
					const auto shadow{ std::sin(pi / 6.0f * settings.LPFDirectCoefficient) * 2.0f };
					const XAUDIO2_FILTER_PARAMETERS filter{ LowPassFilter, std::min(2.0f * std::sin(pi * std::min(air_cutoff(distance), 7350.0f) / 44100.0f) * shadow * mathematics.lerp(1.0f, audio_occlusion_muffle, blocked), muffle), 1.0f };
					const std::float_t send[2] = { audio_reverb_send, audio_reverb_send };

					voice->SetOutputMatrix(master, 1u, output_channels, matrix);
					voice->SetFilterParameters(&filter);

					if (reverb)
					{
						voice->SetOutputMatrix(reverb, 1u, 2u, send);
					}

					voice->SetFrequencyRatio(std::clamp(state.pitch * settings.DopplerFactor, 0.25f, 3.9f));
					voice->SetVolume(level * (1.0f - blocked * audio_occlusion_loss) * effects_level);
				}

				else
				{
					voice->SetVolume(0.0f);
				}

				state.fresh = false;
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void mixer_c::classify()
	{
		const auto kind{ (player.state.flags & structures::movement_underwater) != 0u ? static_cast<std::uint32_t>(structures::acoustic_underwater) : surroundings(listener_position) };

		roofed = world.trace(listener_position, listener_position + structures::vec3_s{ 0.0f, 14.0f, 0.0f }, {}, structures::contents_solid).fraction < 1.0f;

		if (kind != acoustics)
		{
			set_acoustics(kind);
		}
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t mixer_c::surroundings(structures::vec3_s position)
	{
		const auto head{ position };
		const auto roof{ world.trace(head, head + structures::vec3_s{ 0.0f, 14.0f, 0.0f }, {}, structures::contents_solid).fraction < 1.0f };

		auto kind{ static_cast<std::uint32_t>(structures::acoustic_plain) };
		auto walls{ 0u };
		auto close_walls{ 0u };
		auto relief{ 0.0f };

		for (auto ray{ 0u }; ray < 8u; ray++)
		{
			const auto yaw{ two_pi * static_cast<std::float_t>(ray) / 8.0f };
			const structures::vec3_s heading{ std::sin(yaw), 0.0f, std::cos(yaw) };
			const auto hit{ world.trace(head, head + heading * 45.0f, {}, structures::contents_solid) };

			if (hit.fraction < 1.0f && hit.surface != structures::surface_wood)
			{
				walls++;

				close_walls += hit.fraction * 45.0f < 9.0f ? 1u : 0u;
			}

			if (terrain.enabled)
			{
				relief = std::max(relief, terrain.height(head.x + heading.x * 250.0f, head.z + heading.z * 250.0f) - head.y);
			}
		}

		if (roof && close_walls >= 4u)
		{
			kind = structures::acoustic_room;
		}

		else if (walls >= 3u)
		{
			kind = structures::acoustic_city;
		}

		else if (relief > 35.0f)
		{
			kind = structures::acoustic_mountains;
		}

		else if (terrain.enabled && (terrain.biome(head.x, head.z) == structures::biome_woodland || terrain.biome(head.x, head.z) == structures::biome_pinewood))
		{
			kind = structures::acoustic_forest;
		}

		return kind;
	}
	/*
	//=====================================================================================
	*/
	void mixer_c::set_acoustics(std::uint32_t kind)
	{
		if (reverb && kind < structures::acoustic_count)
		{
			XAUDIO2FX_REVERB_PARAMETERS native{};

			ReverbConvertI3DL2ToNative(&acoustic_presets[kind], &native);

			reverb->SetEffectParameters(0u, &native, sizeof(native));

			acoustics = kind;
		}
	}
	/*
	//=====================================================================================
	*/
	std::float_t mixer_c::air_cutoff(std::float_t distance)
	{
		return std::max(700.0f, 16000.0f * std::exp(-distance / 280.0f));
	}
	/*
	//=====================================================================================
	*/
	void mixer_c::update(std::float_t delta)
	{
		if (ready)
		{
			clock += delta;

			const auto drift{ renderer.camera.position - listener_position };

			listener_velocity = mathematics.damp(listener_velocity, delta > 0.0001f && mathematics.length(drift) < audio_listener_speed * delta ? drift / delta : structures::vec3_s{}, 8.0f, delta);
			listener_position = renderer.camera.position;
			listener.Position = { listener_position.x, listener_position.y, listener_position.z };
			listener.Velocity = { listener_velocity.x, listener_velocity.y, listener_velocity.z };
			listener.OrientFront = { renderer.camera.forward.x, renderer.camera.forward.y, renderer.camera.forward.z };
			listener.OrientTop = { renderer.camera.up.x, renderer.camera.up.y, renderer.camera.up.z };

			for (auto index{ 0u }; index < pending.size();)
			{
				if (pending[index].time <= clock)
				{
					launch(pending[index]);

					pending[index] = pending.back();

					pending.pop_back();
				}

				else
				{
					index++;
				}
			}

			acoustic_timer -= delta;

			if (acoustic_timer <= 0.0f)
			{
				acoustic_timer = audio_acoustic_interval;

				classify();
			}

			footsteps(delta);

			mix_ambience(delta);

			place_drones(delta);

			const auto torch_held{ viewmodel.visible && viewmodel.shown_item == structures::item_torch };
			const auto danger{ survival.vitals.dead == false && survival.vitals.health < 35.0f ? 1.0f - survival.vitals.health / 35.0f : 0.0f };

			const auto submerged{ (player.state.flags & structures::movement_underwater) != 0u };

			deafness = std::max(deafness - audio_ring_decay * delta, 0.0f);
			ringing = mathematics.damp(ringing, menu.user.ear_ringing ? mathematics.saturate((deafness - audio_ring_threshold) / (1.0f - audio_ring_threshold)) : 0.0f, 6.0f, delta);
			fire_level = mathematics.damp(fire_level, torch_held && viewmodel.stowed == false ? 0.32f : 0.0f, 4.0f, delta);
			heart_level = mathematics.damp(heart_level, danger * 0.9f, 3.0f, delta);
			underwater_level = mathematics.damp(underwater_level, submerged ? audio_underwater_volume : 0.0f, 7.0f, delta);
			muffle = mathematics.damp(muffle, submerged ? audio_underwater_muffle : mathematics.lerp(1.0f, audio_ring_muffle, ringing), 9.0f, delta);

			if (ring_voice)
			{
				ring_voice->SetVolume(ringing * audio_ring_volume * effects_level);
			}

			if (underwater_voice)
			{
				underwater_voice->SetVolume(underwater_level * ambience_level);
			}

			if (fire_voice)
			{
				fire_voice->SetVolume(fire_level * effects_level);
			}

			if (heart_voice)
			{
				heart_voice->SetVolume(heart_level * effects_level);
				heart_voice->SetFrequencyRatio(1.0f + danger * 0.45f);
			}

			shelter = mathematics.damp(shelter, roofed ? 1.0f : 0.0f, 3.0f, delta);

			if (rain_voice)
			{
				const XAUDIO2_FILTER_PARAMETERS filter{ LowPassFilter, std::min(mathematics.lerp(1.0f, audio_shelter_muffle, shelter), muffle), 1.0f };

				rain_voice->SetVolume(weather.rain_now * (0.55f + weather.storm_now * 0.35f) * (submerged ? audio_underwater_duck : 1.0f) * mathematics.lerp(1.0f, audio_shelter_volume, shelter) * ambience_level);
				rain_voice->SetFilterParameters(&filter);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void mixer_c::footsteps(std::float_t delta)
	{
		const auto speed{ mathematics.length(structures::vec3_s{ player.state.velocity.x, 0.0f, player.state.velocity.z }) };
		const auto step{ std::floor(player.bob_phase + 0.5f) };
		const auto depth{ player.state.water_depth };
		const auto feet{ player.state.position + structures::vec3_s{ 0.0f, 0.1f, 0.0f } };

		if ((player.state.flags & structures::movement_on_ground) && speed > 0.6f && survival.vitals.dead == false && terrain.enabled && step > step_distance)
		{
			play(depth > 0.06f ? structures::sound_wade : surface_sound(player.state.position), feet, std::clamp(0.22f + speed * 0.08f, 0.22f, 0.85f) * ((player.state.flags & structures::movement_crouched) ? 0.4f : 1.0f) * (depth > 0.06f ? 1.2f : 1.0f), 0.92f + random() * 0.16f);
		}

		if ((player.state.flags & structures::movement_swimming) && survival.vitals.dead == false)
		{
			swim_distance += mathematics.length(player.state.velocity) * delta + delta * 0.25f;

			if (swim_distance > swim_stroke_length)
			{
				swim_distance = 0.0f;

				play(structures::sound_swim, feet + structures::vec3_s{ 0.0f, 1.2f, 0.0f }, 0.45f + random() * 0.2f, 0.9f + random() * 0.2f);
			}
		}

		if (previous_depth < 0.35f && depth >= 0.35f && -player.state.velocity.y > water_splash_speed)
		{
			play(structures::sound_splash, feet, std::clamp(-player.state.velocity.y * 0.12f, 0.4f, 1.0f), 0.9f + random() * 0.15f);

			particles.emit(structures::particle_smoke, structures::vec3_s{ player.state.position.x, player.state.water_surface + 0.1f, player.state.position.z }, { 0.0f, 1.2f, 0.0f }, 1.1f, 10u, false);
		}

		previous_depth = depth;
		step_distance = step;
	}
	/*
	//=====================================================================================
	*/
	void mixer_c::mix_ambience(std::float_t delta)
	{
		const auto night{ atmosphere.enabled ? mathematics.smoothstep(0.05f, -0.15f, atmosphere.sun.y) : 0.0f };
		const auto island{ terrain.enabled ? 1.0f : 0.0f };
		const auto height{ player.state.position.y };

		auto town{ 0.0f };

		for (const auto& spot : maps.hotspots)
		{
			town = std::max(town, mathematics.smoothstep(spot.w * 1.7f, spot.w * 0.6f, mathematics.length(structures::vec3_s{ player.state.position.x - spot.x, 0.0f, player.state.position.z - spot.z })));
		}

		coast_timer -= delta;

		if (coast_timer <= 0.0f && terrain.enabled)
		{
			auto nearest{ 0.0f };

			for (auto ring{ 1u }; ring <= 3u; ring++)
			{
				for (auto spoke{ 0u }; spoke < 12u; spoke++)
				{
					const auto radius{ static_cast<std::float_t>(ring * ring) * 14.0f };
					const auto angle{ static_cast<std::float_t>(spoke) / 12.0f * two_pi };

					if (terrain.height(player.state.position.x + std::sin(angle) * radius, player.state.position.z + std::cos(angle) * radius) < sea_level - 0.3f)
					{
						nearest = std::max(nearest, 1.0f - radius / 150.0f);
					}
				}
			}

			coast = nearest;
			coast_timer = 0.5f;
		}

		const auto& mood{ biome_moods[terrain.enabled ? terrain.biome(player.state.position.x, player.state.position.z) : static_cast<std::uint32_t>(structures::biome_meadow)] };
		const std::float_t targets[structures::ambience_count] = { island * (1.0f - night) * (1.0f - coast * 0.7f) * 0.5f * mood.x, island * night * (1.0f - coast * 0.5f) * 0.45f * mood.y, island * (0.1f + town * 0.45f + night * 0.18f), island * std::min(0.16f + mathematics.saturate((height - 10.0f) / 90.0f) * 0.5f + night * 0.08f + mood.z, 0.85f), island * coast * 0.85f };

		const auto hushed{ (player.state.flags & structures::movement_underwater) ? audio_underwater_duck : 1.0f };

		for (auto index{ 0u }; index < structures::ambience_count; index++)
		{
			levels[index] = mathematics.damp(levels[index], targets[index] * hushed, hushed < 1.0f ? 6.0f : 1.2f, delta);

			if (ambience[index])
			{
				ambience[index]->SetVolume(levels[index] * ambience_level);
			}
		}
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t mixer_c::surface_sound(structures::vec3_s position)
	{
		const auto result{ world.trace(position + structures::vec3_s{ 0.0f, 0.3f, 0.0f }, position - structures::vec3_s{ 0.0f, 0.5f, 0.0f }, { 0.1f, 0.05f, 0.1f }, structures::contents_solid) };

		if (result.hit && result.brush >= 0)
		{
			return result.surface == structures::surface_wood ? structures::sound_step_wood : (result.surface == structures::surface_dirt || result.surface == structures::surface_gravel ? structures::sound_step_gravel : (result.surface == structures::surface_sand ? structures::sound_step_soft : (result.surface == structures::surface_grass ? structures::sound_step_grass : structures::sound_step_concrete)));
		}

		if (terrain.enabled)
		{
			return layer_sounds[std::min(terrain.ground(position.x, position.z), terrain_layer_count - 1u)];
		}

		return structures::sound_step_concrete;
	}
	/*
	//=====================================================================================
	*/
	IXAudio2SourceVoice* mixer_c::acquire()
	{
		auto oldest{ 0u };

		for (auto index{ 0u }; index < audio_voices; index++)
		{
			XAUDIO2_VOICE_STATE state{};

			voices[index]->GetState(&state, XAUDIO2_VOICE_NOSAMPLESPLAYED);

			if (state.BuffersQueued == 0u)
			{
				started[index] = clock;

				return voices[index];
			}

			oldest = started[index] < started[oldest] ? index : oldest;
		}

		started[oldest] = clock;

		return voices[oldest];
	}
	/*
	//=====================================================================================
	*/
	std::uint32_t mixer_c::pick(std::uint32_t sound)
	{
		return groups[sound].first + std::min(static_cast<std::uint32_t>(random() * static_cast<std::float_t>(groups[sound].count)), groups[sound].count - 1u);
	}
	/*
	//=====================================================================================
	*/
	std::float_t mixer_c::random()
	{
		seed ^= seed << 13u;
		seed ^= seed >> 17u;
		seed ^= seed << 5u;

		return static_cast<std::float_t>(seed & 0xFFFFFFu) / 16777216.0f;
	}
}

//=====================================================================================
