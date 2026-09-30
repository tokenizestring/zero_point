
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class probes_c
	{
	public:

		structures::vec3_s origin{};
		std::float_t spacing = probe_spacing;
		std::uint32_t count_x = 0u;
		std::uint32_t count_y = 0u;
		std::uint32_t count_z = 0u;
		std::vector<structures::vec4_s> coefficients;
		std::vector<structures::vec4_s> previous;
		std::vector<std::uint8_t> state;
		std::vector<structures::vec3_s> directions;
		std::vector<structures::vec3_s> albedo;
		std::vector<structures::vec3_s> emissive;
		std::vector<structures::light_s> bake_lights;
		ID3D11ShaderResourceView* views[4]{};
		bool enabled = false;

		bool bake(structures::vec3_s bounds_min, structures::vec3_s bounds_max, const std::vector<structures::light_s>& lights, const char* map_name);
		void bake_probe(std::uint32_t index, std::uint32_t pass);
		structures::vec3_s shade_hit(structures::vec3_s position, structures::vec3_s normal, std::uint32_t material, std::uint32_t pass);
		structures::vec3_s sample_irradiance(structures::vec3_s position, structures::vec3_s normal);
		structures::vec3_s sky_radiance(structures::vec3_s direction);
		std::uint64_t compute_hash(const char* map_name);
		bool load_cache(const char* path, std::uint64_t hash);
		void save_cache(const char* path, std::uint64_t hash);
		void upload();
		void destroy();
	};

	extern probes_c probes;
}

//=====================================================================================
