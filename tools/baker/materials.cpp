
//=====================================================================================

#include "baker.hpp"

//=====================================================================================

namespace zp
{
	baker_materials_c baker_materials;

	bool baker_materials_c::bake(const char* assets_directory)
	{
		std::vector<baker::material_job_s> material_jobs;

		for (const auto name : baker::scanned_sets)
		{
			material_jobs.push_back({ name, name, baker::material_origin_scanned, false });
		}

		for (const auto name : baker::neutralized_sets)
		{
			material_jobs.push_back({ std::string(name) + "_grey", name, baker::material_origin_scanned, true });
		}

		for (const auto name : baker::ambientcg_sets)
		{
			material_jobs.push_back({ name, name, baker::material_origin_ambientcg, false });
		}

		for (const auto name : baker::procedural_sets)
		{
			material_jobs.push_back({ name, name, baker::material_origin_procedural, false });
		}

		outputs.resize(material_jobs.size());

		jobs.parallel_for(static_cast<std::uint32_t>(material_jobs.size()), [&](std::uint32_t index)
			{
				const auto& job{ material_jobs[index] };

				baker::material_source_s source{};

				if (job.origin == baker::material_origin_procedural)
				{
					generate(job.source.c_str(), source);
				}

				else if (job.origin == baker::material_origin_ambientcg ? load_ambientcg(assets_directory, job.source.c_str(), source) : load_scanned(assets_directory, job.source.c_str(), source))
				{
					if (job.neutralize)
					{
						neutralize(source);
					}
				}

				else
				{
					logger.write("baker: texture set %s missing, using fallback", job.source.c_str());

					generate("fallback", source);
				}

				finish(job.name.c_str(), job.origin == baker::material_origin_procedural, source, outputs[index]);
			});

		for (const auto& output : outputs)
		{
			logger.write("baker: material %-24s albedo %.3f %.3f %.3f rough %.2f metal %.2f", output.record.name, output.record.average_albedo.x, output.record.average_albedo.y, output.record.average_albedo.z, output.record.average_roughness, output.record.average_metal);
		}

		return outputs.size() == material_jobs.size();
	}
	/*
	//=====================================================================================
	*/
	void baker_materials_c::neutralize(baker::material_source_s& source)
	{
		const auto count{ source.albedo.size() };
		const auto luminance = [](structures::vec3_s color)
			{
				return color.x * 0.2126f + color.y * 0.7152f + color.z * 0.0722f;
			};

		structures::vec3_s paint{};

		for (const auto& color : source.albedo)
		{
			paint += (color - structures::vec3_s{ luminance(color), luminance(color), luminance(color) }) * (1.0f / static_cast<std::float_t>(count));
		}

		const auto direction{ mathematics.normalize(paint) };

		for (auto& color : source.albedo)
		{
			const auto grey{ luminance(color) };
			const auto chroma{ color - structures::vec3_s{ grey, grey, grey } };

			color = mathematics.maximum(structures::vec3_s{ grey, grey, grey } + chroma - direction * std::max(0.0f, mathematics.dot(chroma, direction)), { 0.0f, 0.0f, 0.0f });
		}
	}
	/*
	//=====================================================================================
	*/
	bool baker_materials_c::load_ambientcg(const char* assets_directory, const char* name, baker::material_source_s& source)
	{
		const auto base{ std::string(assets_directory) + "\\raw\\textures_acg\\" + name + "\\" + name + "_2K-JPG_" };

		baker::image_s color{}, normal{}, roughness{}, occlusion{}, metalness{}, displacement{}, opacity{};

		const auto has_color{ baker_images.load((base + "Color.jpg").c_str(), color) };
		const auto has_normal{ baker_images.load((base + "NormalDX.jpg").c_str(), normal) };
		const auto has_roughness{ baker_images.load((base + "Roughness.jpg").c_str(), roughness) };
		const auto has_occlusion{ baker_images.load((base + "AmbientOcclusion.jpg").c_str(), occlusion) };
		const auto has_metalness{ baker_images.load((base + "Metalness.jpg").c_str(), metalness) };
		const auto has_displacement{ baker_images.load((base + "Displacement.jpg").c_str(), displacement) };
		const auto has_opacity{ baker_images.load((base + "Opacity.jpg").c_str(), opacity) };

		if (has_color && has_normal && has_roughness)
		{
			source.aspect = static_cast<std::float_t>(color.width) / static_cast<std::float_t>(std::max(1u, color.height));

			for (auto image : { &color, &normal, &roughness, &occlusion, &metalness, &displacement, &opacity })
			{
				if (image->pixels.size())
				{
					baker_images.resize(*image, material_texture_size, material_texture_size);
				}
			}

			const auto count{ static_cast<std::size_t>(material_texture_size) * material_texture_size };

			source.size = material_texture_size;
			source.albedo.resize(count);
			source.normal.resize(count);
			source.roughness.resize(count);
			source.occlusion.resize(count);
			source.height.resize(count);
			source.metal.resize(count);

			if (has_opacity)
			{
				source.alpha.resize(count);
			}

			for (auto index{ 0u }; index < count; index++)
			{
				source.albedo[index] = { baker_images.srgb_to_linear(color.pixels[index].x), baker_images.srgb_to_linear(color.pixels[index].y), baker_images.srgb_to_linear(color.pixels[index].z) };
				source.normal[index] = mathematics.normalize({ normal.pixels[index].x * 2.0f - 1.0f, normal.pixels[index].y * 2.0f - 1.0f, normal.pixels[index].z * 2.0f - 1.0f });
				source.roughness[index] = roughness.pixels[index].x;
				source.occlusion[index] = has_occlusion ? occlusion.pixels[index].x : 1.0f;
				source.metal[index] = has_metalness ? metalness.pixels[index].x : 0.0f;
				source.height[index] = has_displacement ? displacement.pixels[index].x : 0.5f;

				if (has_opacity)
				{
					source.alpha[index] = opacity.pixels[index].x;
				}
			}

			return true;
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	bool baker_materials_c::load_scanned(const char* assets_directory, const char* name, baker::material_source_s& source)
	{
		char path[MAX_PATH]{};

		baker::image_s diffuse{}, normal{}, arm{}, displacement{};

		std::snprintf(path, sizeof(path), "%s\\raw\\textures\\%s\\%s_diff_2k.jpg", assets_directory, name, name);
		const auto loaded_diffuse{ baker_images.load(path, diffuse) };

		std::snprintf(path, sizeof(path), "%s\\raw\\textures\\%s\\%s_nor_dx_2k.jpg", assets_directory, name, name);
		const auto loaded_normal{ baker_images.load(path, normal) };

		std::snprintf(path, sizeof(path), "%s\\raw\\textures\\%s\\%s_arm_2k.jpg", assets_directory, name, name);
		const auto loaded_arm{ baker_images.load(path, arm) };

		std::snprintf(path, sizeof(path), "%s\\raw\\textures\\%s\\%s_disp_2k.jpg", assets_directory, name, name);
		const auto loaded_displacement{ baker_images.load(path, displacement) };

		if (loaded_diffuse && loaded_normal && loaded_arm && loaded_displacement)
		{
			source.aspect = static_cast<std::float_t>(diffuse.width) / static_cast<std::float_t>(std::max(1u, diffuse.height));

			for (auto image : { &diffuse, &normal, &arm, &displacement })
			{
				baker_images.resize(*image, material_texture_size, material_texture_size);
			}

			if (diffuse.pixels.size() == static_cast<std::size_t>(material_texture_size) * material_texture_size)
			{
				const auto count{ static_cast<std::size_t>(material_texture_size) * material_texture_size };

				source.size = material_texture_size;
				source.albedo.resize(count);
				source.normal.resize(count);
				source.roughness.resize(count);
				source.occlusion.resize(count);
				source.height.resize(count);
				source.metal.resize(count);

				for (auto index{ 0u }; index < count; index++)
				{
					source.albedo[index] = { baker_images.srgb_to_linear(diffuse.pixels[index].x), baker_images.srgb_to_linear(diffuse.pixels[index].y), baker_images.srgb_to_linear(diffuse.pixels[index].z) };
					source.normal[index] = mathematics.normalize({ normal.pixels[index].x * 2.0f - 1.0f, normal.pixels[index].y * 2.0f - 1.0f, normal.pixels[index].z * 2.0f - 1.0f });
					source.occlusion[index] = arm.pixels[index].x;
					source.roughness[index] = arm.pixels[index].y;
					source.metal[index] = arm.pixels[index].z;
					source.height[index] = displacement.pixels[index].x;
				}

				return true;
			}
		}

		return false;
	}
	/*
	//=====================================================================================
	*/
	void baker_materials_c::generate(const char* name, baker::material_source_s& source)
	{
		const auto size{ baker::procedural_size };
		const auto count{ static_cast<std::size_t>(size) * size };
		const auto kind{ functions::hash(name) };

		source.size = size;
		source.aspect = 1.0f;
		source.albedo.assign(count, { 0.18f, 0.18f, 0.18f });
		source.normal.assign(count, { 0.0f, 0.0f, 1.0f });
		source.roughness.assign(count, 0.6f);
		source.occlusion.assign(count, 1.0f);
		source.height.assign(count, 0.5f);
		source.metal.assign(count, 0.0f);

		std::vector<std::float_t> scratches;

		const auto scratch_field = [&](std::uint32_t amount, std::float_t base_angle, std::float_t spread, std::uint32_t seed)
			{
				scratches.assign(count, 0.0f);

				for (auto scratch{ 0u }; scratch < amount; scratch++)
				{
					const auto x0{ baker_images.hash(static_cast<std::int32_t>(scratch), 1, seed) * static_cast<std::float_t>(size) };
					const auto y0{ baker_images.hash(static_cast<std::int32_t>(scratch), 2, seed) * static_cast<std::float_t>(size) };
					const auto angle{ base_angle + (baker_images.hash(static_cast<std::int32_t>(scratch), 3, seed) - 0.5f) * spread };
					const auto length{ (0.02f + 0.22f * std::pow(baker_images.hash(static_cast<std::int32_t>(scratch), 4, seed), 2.0f)) * static_cast<std::float_t>(size) };
					const auto strength{ 0.35f + 0.65f * baker_images.hash(static_cast<std::int32_t>(scratch), 5, seed) };

					for (auto step{ 0.0f }; step < length; step += 0.5f)
					{
						const auto px{ static_cast<std::int32_t>(x0 + std::cos(angle) * step) };
						const auto py{ static_cast<std::int32_t>(y0 + std::sin(angle) * step) };
						const auto wx{ ((px % static_cast<std::int32_t>(size)) + static_cast<std::int32_t>(size)) % static_cast<std::int32_t>(size) };
						const auto wy{ ((py % static_cast<std::int32_t>(size)) + static_cast<std::int32_t>(size)) % static_cast<std::int32_t>(size) };
						const auto fade{ std::sin(step / length * pi) };

						auto& cell{ scratches[static_cast<std::size_t>(wy) * size + wx] };

						cell = std::max(cell, strength * fade);
					}
				}
			};

		const auto streaks = [&](std::float_t u, std::float_t v, std::int32_t across, std::int32_t along, std::uint32_t seed)
			{
				const auto x{ u * static_cast<std::float_t>(across) };
				const auto y{ v * static_cast<std::float_t>(along) };
				const auto ix{ static_cast<std::int32_t>(std::floor(x)) };
				const auto iy{ static_cast<std::int32_t>(std::floor(y)) };
				const auto fx{ x - std::floor(x) };
				const auto fy{ y - std::floor(y) };

				const auto corner = [&](std::int32_t cx, std::int32_t cy)
					{
						return baker_images.hash(((cx % across) + across) % across, ((cy % along) + along) % along, seed);
					};

				return mathematics.lerp(mathematics.lerp(corner(ix, iy), corner(ix + 1, iy), fx * fx * (3.0f - 2.0f * fx)), mathematics.lerp(corner(ix, iy + 1), corner(ix + 1, iy + 1), fx * fx * (3.0f - 2.0f * fx)), fy * fy * (3.0f - 2.0f * fy));
			};

		auto strength{ 4.0f };

		if (kind == functions::hash("anodized") || kind == functions::hash("painted_steel"))
		{
			scratch_field(kind == functions::hash("anodized") ? 700u : 260u, 0.15f, 0.9f, kind == functions::hash("anodized") ? 5u : 6u);
		}

		for (auto y{ 0u }; y < size; y++)
		{
			for (auto x{ 0u }; x < size; x++)
			{
				const auto index{ static_cast<std::size_t>(y) * size + x };
				const auto u{ (static_cast<std::float_t>(x) + 0.5f) / static_cast<std::float_t>(size) };
				const auto v{ (static_cast<std::float_t>(y) + 0.5f) / static_cast<std::float_t>(size) };

				auto& albedo{ source.albedo[index] };
				auto& roughness{ source.roughness[index] };
				auto& occlusion{ source.occlusion[index] };
				auto& height{ source.height[index] };
				auto& metal{ source.metal[index] };

				if (kind == functions::hash("polymer"))
				{
					const auto stipple{ baker_images.fbm(u * 96.0f, v * 96.0f, 96, 3u, 0.55f, 11u) };
					const auto mottle{ baker_images.fbm(u * 6.0f, v * 6.0f, 6, 4u, 0.5f, 12u) };

					albedo = structures::vec3_s{ 0.042f, 0.043f, 0.045f } * (1.0f + 0.3f * mottle);
					roughness = std::clamp(0.62f + 0.12f * mottle + 0.12f * stipple, 0.0f, 1.0f);
					height = 0.5f + 0.25f * stipple;

					strength = 3.0f;
				}

				else if (kind == functions::hash("anodized"))
				{
					const auto streak{ streaks(u, v, 6, 720, 13u) };
					const auto scratch{ scratches[index] };

					albedo = mathematics.lerp(structures::vec3_s{ 0.035f, 0.035f, 0.037f } * (0.92f + 0.16f * streak), structures::vec3_s{ 0.62f, 0.62f, 0.63f }, scratch * 0.85f);
					roughness = std::clamp(0.3f + 0.08f * streak - 0.08f * scratch, 0.0f, 1.0f);
					height = 0.5f + 0.03f * streak - 0.35f * scratch;
					metal = 1.0f;

					strength = 3.0f;
				}

				else if (kind == functions::hash("steel"))
				{
					const auto streak{ streaks(u, v, 5, 900, 14u) };
					const auto broad{ baker_images.fbm(u * 4.0f, v * 4.0f, 4, 4u, 0.5f, 15u) };

					albedo = structures::vec3_s{ 0.56f, 0.57f, 0.58f } * (0.93f + 0.1f * streak + 0.04f * broad);
					roughness = std::clamp(0.24f + 0.14f * streak + 0.06f * broad, 0.0f, 1.0f);
					height = 0.5f + 0.08f * streak;
					metal = 1.0f;

					strength = 2.0f;
				}

				else if (kind == functions::hash("carbon"))
				{
					const auto tows{ 24.0f };
					const auto cu{ u * tows };
					const auto cv{ v * tows };
					const auto i{ static_cast<std::int32_t>(std::floor(cu)) };
					const auto j{ static_cast<std::int32_t>(std::floor(cv)) };
					const auto fu{ cu - std::floor(cu) };
					const auto fv{ cv - std::floor(cv) };
					const auto warp_on_top{ ((i + j) & 3) < 2 };
					const auto profile{ warp_on_top ? std::sin(fu * pi) : std::sin(fv * pi) };
					const auto fibers{ 0.92f + 0.08f * std::sin((warp_on_top ? fu : fv) * pi * 18.0f) };

					albedo = structures::vec3_s{ 0.02f, 0.021f, 0.023f } * (warp_on_top ? 1.45f : 0.85f) * fibers * (0.8f + 0.4f * profile);
					roughness = 0.17f + 0.05f * (1.0f - profile);
					height = 0.35f + 0.55f * profile * (warp_on_top ? 1.0f : 0.9f);
					occlusion = 0.72f + 0.28f * profile;

					strength = 5.0f;
				}

				else if (kind == functions::hash("rubber"))
				{
					const auto cell{ baker_images.voronoi(u * 40.0f, v * 40.0f, 40, 21u) };
					const auto dome{ std::pow(std::clamp(1.0f - cell.f1 / 0.42f, 0.0f, 1.0f), 0.7f) };
					const auto grain{ baker_images.fbm(u * 64.0f, v * 64.0f, 64, 3u, 0.5f, 22u) };

					albedo = structures::vec3_s{ 0.03f, 0.03f, 0.031f } * (0.9f + 0.2f * grain);
					roughness = std::clamp(0.84f + 0.08f * grain - 0.12f * dome, 0.0f, 1.0f);
					height = 0.2f + 0.8f * dome;
					occlusion = 0.72f + 0.28f * dome;

					strength = 9.0f;
				}

				else if (kind == functions::hash("fabric") || kind == functions::hash("nylon"))
				{
					const auto nylon{ kind == functions::hash("nylon") };
					const auto threads{ nylon ? 56.0f : 110.0f };
					const auto cu{ u * threads };
					const auto cv{ v * threads };
					const auto i{ static_cast<std::int32_t>(std::floor(cu)) };
					const auto j{ static_cast<std::int32_t>(std::floor(cv)) };
					const auto fu{ cu - std::floor(cu) };
					const auto fv{ cv - std::floor(cv) };
					const auto over{ nylon ? (((i / 2) + (j / 2)) & 1) == 0 : ((i + j) & 1) == 0 };
					const auto warp{ std::sin(fu * pi) * (over ? 1.0f : 0.45f) };
					const auto weft{ std::sin(fv * pi) * (over ? 0.45f : 1.0f) };
					const auto fuzz{ baker_images.fbm(u * 128.0f, v * 128.0f, 128, 3u, 0.5f, 23u) };
					const auto broad{ baker_images.fbm(u * 5.0f, v * 5.0f, 5, 4u, 0.5f, 24u) };
					const auto thread_tone{ 0.9f + 0.2f * baker_images.hash(warp > weft ? i : j, warp > weft ? 7 : 9, 25u) };

					albedo = structures::vec3_s{ 0.34f, 0.34f, 0.34f } * thread_tone * (0.88f + 0.14f * broad + 0.05f * fuzz) * (nylon ? 0.78f : 1.0f);
					roughness = std::clamp((nylon ? 0.66f : 0.9f) + 0.06f * fuzz, 0.0f, 1.0f);
					height = std::max(warp, weft) * 0.85f + 0.08f * fuzz;
					occlusion = 0.62f + 0.38f * std::max(warp, weft);

					strength = nylon ? 7.0f : 5.0f;
				}

				else if (kind == functions::hash("skin"))
				{
					const auto blotch{ baker_images.fbm(u * 6.0f, v * 6.0f, 6, 5u, 0.5f, 31u) };
					const auto pore_cell{ baker_images.voronoi(u * 190.0f, v * 190.0f, 190, 32u) };
					const auto pore{ std::clamp(1.0f - pore_cell.f1 / 0.16f, 0.0f, 1.0f) };
					const auto wrinkle{ baker_images.ridged(u * 12.0f, v * 12.0f, 12, 4u, 33u) };

					albedo = structures::vec3_s{ 0.56f + 0.06f * blotch, 0.37f - 0.02f * blotch, 0.3f - 0.02f * blotch } * (1.0f - 0.18f * pore);
					roughness = std::clamp(0.52f + 0.14f * blotch + 0.18f * pore, 0.0f, 1.0f);
					height = 0.5f - 0.35f * pore + 0.12f * wrinkle;
					occlusion = 1.0f - 0.25f * pore;

					strength = 3.0f;
				}

				else if (kind == functions::hash("flesh"))
				{
					const auto sinew{ baker_images.ridged(u * 8.0f, v * 8.0f, 8, 5u, 41u) };
					const auto veins{ std::pow(baker_images.ridged(u * 3.0f, v * 3.0f, 3, 4u, 42u), 6.0f) };
					const auto lumps{ baker_images.fbm(u * 10.0f, v * 10.0f, 10, 5u, 0.55f, 43u) };

					albedo = mathematics.lerp(mathematics.lerp(structures::vec3_s{ 0.11f, 0.012f, 0.014f }, structures::vec3_s{ 0.34f, 0.045f, 0.035f }, sinew), structures::vec3_s{ 0.06f, 0.01f, 0.04f }, veins * 0.7f);
					roughness = std::clamp(0.26f + 0.22f * (1.0f - sinew) + 0.05f * lumps, 0.0f, 1.0f);
					height = 0.35f + 0.4f * sinew + 0.25f * lumps;
					occlusion = 0.65f + 0.35f * sinew;

					strength = 7.0f;
				}

				else if (kind == functions::hash("panel"))
				{
					const auto pu{ u * 4.0f };
					const auto pv{ v * 4.0f };
					const auto ci{ static_cast<std::int32_t>(std::floor(pu)) };
					const auto cj{ static_cast<std::int32_t>(std::floor(pv)) };
					const auto lu{ pu - std::floor(pu) };
					const auto lv{ pv - std::floor(pv) };
					const auto split{ baker_images.hash(ci, cj, 51u) };
					const auto pixels_per_panel{ static_cast<std::float_t>(size) / 4.0f };

					auto seam{ std::min(std::min(lu, 1.0f - lu), std::min(lv, 1.0f - lv)) };
					auto sub_u{ lu };
					auto sub_v{ lv };

					if (split < 0.4f)
					{
						seam = std::min(seam, std::fabs(lu - 0.5f));

						sub_u = lu < 0.5f ? lu * 2.0f : (lu - 0.5f) * 2.0f;
					}

					else if (split < 0.7f)
					{
						seam = std::min(seam, std::fabs(lv - 0.5f));

						sub_v = lv < 0.5f ? lv * 2.0f : (lv - 0.5f) * 2.0f;
					}

					const auto seam_pixels{ seam * pixels_per_panel };
					const auto groove{ mathematics.smoothstep(1.5f, 4.5f, seam_pixels) };
					const auto grime{ baker_images.fbm(u * 9.0f, v * 9.0f, 9, 5u, 0.55f, 52u) };
					const auto wear_noise{ baker_images.fbm(u * 40.0f, v * 40.0f, 40, 4u, 0.5f, 53u) };
					const auto wear{ (seam_pixels > 3.0f && seam_pixels < 9.0f && wear_noise > 0.28f) ? 1.0f : 0.0f };
					const auto tone{ 0.9f + 0.18f * baker_images.hash(ci * 2 + (sub_u > 0.5f ? 1 : 0), cj * 2 + (sub_v > 0.5f ? 1 : 0), 54u) };
					const auto bolt_distance{ std::min(std::min(std::hypot((sub_u - 0.07f) * pixels_per_panel, (sub_v - 0.07f) * pixels_per_panel), std::hypot((sub_u - 0.93f) * pixels_per_panel, (sub_v - 0.07f) * pixels_per_panel)), std::min(std::hypot((sub_u - 0.07f) * pixels_per_panel, (sub_v - 0.93f) * pixels_per_panel), std::hypot((sub_u - 0.93f) * pixels_per_panel, (sub_v - 0.93f) * pixels_per_panel))) };
					const auto bolt{ std::clamp(1.0f - bolt_distance / 5.5f, 0.0f, 1.0f) };

					albedo = mathematics.lerp(structures::vec3_s{ 0.36f, 0.365f, 0.37f } * tone * (0.9f + 0.1f * grime), structures::vec3_s{ 0.55f, 0.55f, 0.56f }, std::max(wear, bolt > 0.0f ? 0.6f : 0.0f));
					metal = std::max(wear, bolt > 0.0f ? 1.0f : 0.0f);
					roughness = std::clamp(0.48f + 0.12f * grime - 0.15f * metal, 0.0f, 1.0f);
					height = 0.15f + 0.6f * groove + 0.25f * std::sqrt(bolt) - 0.04f * wear;
					occlusion = 0.5f + 0.5f * mathematics.smoothstep(0.0f, 14.0f, seam_pixels);

					strength = 10.0f;
				}

				else if (kind == functions::hash("hexgrid"))
				{
					const auto columns{ 12.0f };
					const auto rows{ 14.0f };
					const auto hx{ u * columns };
					const auto hy{ v * rows * 0.8660254f };

					auto best{ 1e9f };
					auto second{ 1e9f };
					auto best_cell{ 0 };

					for (auto oy{ -1 }; oy <= 2; oy++)
					{
						for (auto ox{ -1 }; ox <= 2; ox++)
						{
							const auto row{ static_cast<std::int32_t>(std::floor(v * rows)) + oy };
							const auto column{ static_cast<std::int32_t>(std::floor(hx)) + ox };
							const auto center_x{ static_cast<std::float_t>(column) + ((row & 1) ? 0.5f : 0.0f) };
							const auto center_y{ static_cast<std::float_t>(row) * 0.8660254f };
							const auto distance{ std::hypot(hx - center_x, hy - center_y) };

							if (distance < best)
							{
								second = best;
								best = distance;
								best_cell = (((row % 14) + 14) % 14) * 12 + (((column % 12) + 12) % 12);
							}

							else if (distance < second)
							{
								second = distance;
							}
						}
					}

					const auto edge{ (second - best) * 0.5f };
					const auto plate{ mathematics.smoothstep(0.02f, 0.07f, edge) };
					const auto tone{ baker_images.hash(best_cell, 3, 61u) };

					albedo = structures::vec3_s{ 0.07f, 0.075f, 0.08f } * (0.85f + 0.3f * tone);
					metal = 0.85f;
					roughness = 0.3f + 0.15f * tone + 0.2f * (1.0f - plate);
					height = 0.2f + 0.8f * plate;
					occlusion = 0.55f + 0.45f * plate;

					strength = 8.0f;
				}

				else if (kind == functions::hash("glass"))
				{
					const auto smudge{ baker_images.fbm(u * 5.0f, v * 5.0f, 5, 6u, 0.55f, 71u) };

					albedo = { 0.9f, 0.92f, 0.94f };
					roughness = std::clamp(0.03f + 0.14f * std::max(0.0f, smudge * 1.6f + 0.15f), 0.0f, 1.0f);
					height = 0.5f;

					strength = 0.0f;
				}

				else if (kind == functions::hash("knurled"))
				{
					const auto density{ 48.0f };
					const auto a{ (u + v) * density - std::floor((u + v) * density) };
					const auto b{ (u - v) * density - std::floor((u - v) * density) };
					const auto pyramid{ std::min(1.0f - std::fabs(2.0f * a - 1.0f), 1.0f - std::fabs(2.0f * b - 1.0f)) };

					albedo = { 0.58f, 0.58f, 0.59f };
					metal = 1.0f;
					roughness = 0.32f + 0.12f * (1.0f - pyramid);
					height = pyramid;
					occlusion = 0.7f + 0.3f * pyramid;

					strength = 12.0f;
				}

				else if (kind == functions::hash("painted_steel"))
				{
					const auto chips{ mathematics.smoothstep(0.3f, 0.34f, baker_images.fbm(u * 10.0f, v * 10.0f, 10, 5u, 0.55f, 81u)) };
					const auto exposed{ std::max(chips, scratches[index] * 0.9f) };
					const auto grime{ baker_images.fbm(u * 7.0f, v * 7.0f, 7, 5u, 0.5f, 82u) };

					albedo = mathematics.lerp(structures::vec3_s{ 0.4f, 0.4f, 0.4f } * (0.92f + 0.12f * grime), structures::vec3_s{ 0.52f, 0.52f, 0.53f }, exposed);
					metal = exposed;
					roughness = std::clamp(0.44f + 0.1f * grime - 0.14f * exposed, 0.0f, 1.0f);
					height = 0.62f - 0.22f * exposed;
					occlusion = 0.9f + 0.1f * grime;

					strength = 6.0f;
				}

				else
				{
					albedo = { 0.3f, 0.3f, 0.3f };
					roughness = 0.7f;

					strength = 0.0f;
				}
			}
		}

		normals_from_height(source, strength);
	}
	/*
	//=====================================================================================
	*/
	void baker_materials_c::normals_from_height(baker::material_source_s& source, std::float_t strength)
	{
		const auto size{ source.size };

		for (auto y{ 0u }; y < size; y++)
		{
			for (auto x{ 0u }; x < size; x++)
			{
				const auto left{ source.height[static_cast<std::size_t>(y) * size + (x + size - 1u) % size] };
				const auto right{ source.height[static_cast<std::size_t>(y) * size + (x + 1u) % size] };
				const auto up{ source.height[static_cast<std::size_t>((y + size - 1u) % size) * size + x] };
				const auto down{ source.height[static_cast<std::size_t>((y + 1u) % size) * size + x] };

				source.normal[static_cast<std::size_t>(y) * size + x] = mathematics.normalize({ -(right - left) * 0.5f * strength, -(down - up) * 0.5f * strength, 1.0f });
			}
		}
	}
	/*
	//=====================================================================================
	*/
	void baker_materials_c::finish(const char* name, bool procedural, baker::material_source_s& source, baker::material_output_s& output)
	{
		output = {};

		std::snprintf(output.record.name, sizeof(output.record.name), "%s", name);

		output.record.procedural = procedural ? 1u : 0u;
		output.record.height_scale = procedural ? 0.004f : 0.02f;
		output.record.aspect = source.aspect > 0.0f ? source.aspect : 1.0f;

		const auto base_count{ static_cast<std::size_t>(source.size) * source.size };

		structures::vec3_s albedo_sum{};

		auto roughness_sum{ 0.0 };
		auto metal_sum{ 0.0 };

		for (auto index{ 0u }; index < base_count; index++)
		{
			albedo_sum += source.albedo[index] * (1.0f / static_cast<std::float_t>(base_count));

			roughness_sum += source.roughness[index];

			metal_sum += source.metal[index];
		}

		output.record.average_albedo = albedo_sum;
		output.record.average_roughness = static_cast<std::float_t>(roughness_sum / static_cast<std::double_t>(base_count));
		output.record.average_metal = static_cast<std::float_t>(metal_sum / static_cast<std::double_t>(base_count));

		auto size{ source.size };

		std::vector<std::uint8_t> rgba, normal_rg, rough_ao, height_metal;

		const auto coverage_target{ coverage(source.alpha, base_count, 1.0f) };

		while (size >= 1u)
		{
			const auto count{ static_cast<std::size_t>(size) * size };

			auto low{ 0.25f };
			auto high{ 8.0f };

			for (auto step{ 0u }; source.alpha.size() && step < 18u; step++)
			{
				if (coverage(source.alpha, count, (low + high) * 0.5f) < coverage_target)
				{
					low = (low + high) * 0.5f;
				}

				else
				{
					high = (low + high) * 0.5f;
				}
			}

			const auto alpha_scale{ source.alpha.size() ? (low + high) * 0.5f : 1.0f };

			rgba.resize(count * 4u);
			normal_rg.resize(count * 2u);
			rough_ao.resize(count * 2u);
			height_metal.resize(count * 2u);

			for (auto index{ 0u }; index < count; index++)
			{
				const auto albedo{ source.albedo[index] };
				const auto normal{ mathematics.normalize(source.normal[index]) };
				const auto spread{ std::clamp(mathematics.length(source.normal[index]), 0.0f, 1.0f) };

				auto roughness{ std::clamp(source.roughness[index], 0.02f, 1.0f) };

				if (spread < 0.9999f && spread > 0.0001f)
				{
					const auto kappa{ (3.0f * spread - spread * spread * spread) / (1.0f - spread * spread) };
					const auto alpha{ roughness * roughness };

					roughness = std::sqrt(std::sqrt(alpha * alpha + 1.0f / kappa));
				}

				rgba[index * 4u + 0u] = static_cast<std::uint8_t>(std::clamp(baker_images.linear_to_srgb(std::clamp(albedo.x, 0.0f, 1.0f)) * 255.0f + 0.5f, 0.0f, 255.0f));
				rgba[index * 4u + 1u] = static_cast<std::uint8_t>(std::clamp(baker_images.linear_to_srgb(std::clamp(albedo.y, 0.0f, 1.0f)) * 255.0f + 0.5f, 0.0f, 255.0f));
				rgba[index * 4u + 2u] = static_cast<std::uint8_t>(std::clamp(baker_images.linear_to_srgb(std::clamp(albedo.z, 0.0f, 1.0f)) * 255.0f + 0.5f, 0.0f, 255.0f));
				rgba[index * 4u + 3u] = source.alpha.size() ? static_cast<std::uint8_t>(std::clamp(source.alpha[index] * alpha_scale * 255.0f + 0.5f, 0.0f, 255.0f)) : 255u;

				normal_rg[index * 2u + 0u] = static_cast<std::uint8_t>(std::clamp(normal.x * 127.5f + 127.5f, 0.0f, 255.0f));
				normal_rg[index * 2u + 1u] = static_cast<std::uint8_t>(std::clamp(normal.y * 127.5f + 127.5f, 0.0f, 255.0f));

				rough_ao[index * 2u + 0u] = static_cast<std::uint8_t>(std::clamp(roughness * 255.0f + 0.5f, 0.0f, 255.0f));
				rough_ao[index * 2u + 1u] = static_cast<std::uint8_t>(std::clamp(source.occlusion[index] * 255.0f + 0.5f, 0.0f, 255.0f));

				height_metal[index * 2u + 0u] = static_cast<std::uint8_t>(std::clamp(source.height[index] * 255.0f + 0.5f, 0.0f, 255.0f));
				height_metal[index * 2u + 1u] = static_cast<std::uint8_t>(std::clamp(source.metal[index] * 255.0f + 0.5f, 0.0f, 255.0f));
			}

			baker_compressor.compress_bc7(rgba.data(), size, size, output.albedo);
			baker_compressor.compress_bc5(normal_rg.data(), size, size, output.normal);
			baker_compressor.compress_bc5(rough_ao.data(), size, size, output.rough_ao);
			baker_compressor.compress_bc5(height_metal.data(), size, size, output.height_metal);

			if (size > 1u)
			{
				const auto next{ size / 2u };

				for (auto y{ 0u }; y < next; y++)
				{
					for (auto x{ 0u }; x < next; x++)
					{
						const auto a{ static_cast<std::size_t>(y * 2u) * size + x * 2u };
						const auto b{ a + 1u };
						const auto c{ a + size };
						const auto d{ c + 1u };
						const auto target{ static_cast<std::size_t>(y) * next + x };

						source.albedo[target] = (source.albedo[a] + source.albedo[b] + source.albedo[c] + source.albedo[d]) * 0.25f;
						source.normal[target] = (source.normal[a] + source.normal[b] + source.normal[c] + source.normal[d]) * 0.25f;
						source.roughness[target] = (source.roughness[a] + source.roughness[b] + source.roughness[c] + source.roughness[d]) * 0.25f;
						source.occlusion[target] = (source.occlusion[a] + source.occlusion[b] + source.occlusion[c] + source.occlusion[d]) * 0.25f;
						source.height[target] = (source.height[a] + source.height[b] + source.height[c] + source.height[d]) * 0.25f;
						source.metal[target] = (source.metal[a] + source.metal[b] + source.metal[c] + source.metal[d]) * 0.25f;

						if (source.alpha.size())
						{
							source.alpha[target] = (source.alpha[a] + source.alpha[b] + source.alpha[c] + source.alpha[d]) * 0.25f;
						}
					}
				}
			}

			size /= 2u;
		}

		output.valid = true;
	}
	/*
	//=====================================================================================
	*/
	std::float_t baker_materials_c::coverage(const std::vector<std::float_t>& alpha, std::size_t count, std::float_t scale)
	{
		auto covered{ 0u };

		for (auto index{ 0u }; index < count && index < alpha.size(); index++)
		{
			covered += alpha[index] * scale > 0.5f ? 1u : 0u;
		}

		return count ? static_cast<std::float_t>(covered) / static_cast<std::float_t>(count) : 0.0f;
	}
	/*
	//=====================================================================================
	*/
	void baker_materials_c::append_items(std::vector<baker::pak_item_s>& items)
	{
		const auto layers{ static_cast<std::uint32_t>(outputs.size()) };

		auto mips{ 0u };

		for (auto size{ material_texture_size }; size >= 1u; size /= 2u)
		{
			mips++;
		}

		const struct
		{
			const char* name;
			DXGI_FORMAT format;
			std::vector<std::uint8_t> baker::material_output_s::* member;
		}
		arrays[] =
		{
			{ "materials_albedo", DXGI_FORMAT_BC7_UNORM_SRGB, &baker::material_output_s::albedo },
			{ "materials_normal", DXGI_FORMAT_BC5_UNORM, &baker::material_output_s::normal },
			{ "materials_rough_ao", DXGI_FORMAT_BC5_UNORM, &baker::material_output_s::rough_ao },
			{ "materials_height_metal", DXGI_FORMAT_BC5_UNORM, &baker::material_output_s::height_metal }
		};

		for (const auto& array : arrays)
		{
			baker::pak_item_s item{};

			std::snprintf(item.entry.name, sizeof(item.entry.name), "%s", array.name);

			item.entry.type = structures::pak_type_texture_array;
			item.entry.format = static_cast<std::uint32_t>(array.format);
			item.entry.width = material_texture_size;
			item.entry.height = material_texture_size;
			item.entry.layers = layers;
			item.entry.mips = mips;

			for (const auto& output : outputs)
			{
				const auto& bytes{ output.*array.member };

				item.data.insert(item.data.end(), bytes.begin(), bytes.end());
			}

			items.push_back(std::move(item));
		}

		baker::pak_item_s table{};

		std::snprintf(table.entry.name, sizeof(table.entry.name), "%s", "materials_table");

		table.entry.type = structures::pak_type_blob;
		table.entry.layers = layers;

		for (const auto& output : outputs)
		{
			const auto bytes{ reinterpret_cast<const std::uint8_t*>(&output.record) };

			table.data.insert(table.data.end(), bytes, bytes + sizeof(output.record));
		}

		items.push_back(std::move(table));
	}
}

//=====================================================================================
