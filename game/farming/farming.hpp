
//=====================================================================================

#pragma once

#include "../../core/engine/engine.hpp"

//=====================================================================================

namespace zp
{
	class farming_c
	{
	public:

		std::vector<structures::crop_s> crops;
		std::vector<structures::vec4_s> springs;
		builder_c pool_builder;
		structures::mesh_s pool{};
		const structures::model_s* shapes[structures::crop_count]{};
		const structures::model_s* mound = nullptr;
		structures::vec3_s ghost{};
		std::uint32_t withered = 0u;
		std::uint32_t revision = 0u;
		std::uint32_t seed = 0x6C8E9CF5u;
		std::uint32_t ghost_kind = structures::crop_none;
		bool ghosting = false;

		void clear();
		void create_models();
		void create_potato(const char* name);
		void create_corn(const char* name);
		void create_pumpkin(const char* name);
		void create_mound(const char* name);
		void update(std::float_t delta, bool input_enabled);
		void grow(std::float_t delta);
		bool plant(std::uint32_t kind, structures::vec3_s position);
		bool sow(survival_c& owner, std::uint32_t slot, structures::vec3_s spot);
		void water(std::uint32_t index, survival_c& owner, std::uint32_t slot);
		void drink(survival_c& owner, structures::vec3_s origin, structures::vec3_s forward);
		void reap(std::uint32_t index, survival_c& owner);
		bool soil(structures::vec3_s origin, structures::vec3_s forward, structures::vec3_s& out);
		bool fertile(structures::vec3_s point);
		std::int32_t crop_near(structures::vec3_s position);
		std::int32_t crop_target(structures::vec3_s origin, structures::vec3_s forward);
		std::int32_t well_target(structures::vec3_s origin, structures::vec3_s forward);
		std::int32_t spring_target(structures::vec3_s origin, structures::vec3_s forward);
		void destroy();
		bool sea_target(structures::vec3_s origin, structures::vec3_s forward);
		bool irrigated(structures::vec3_s position);
		void submit();
		std::float_t random();
	};

	extern farming_c farming;
}

//=====================================================================================
