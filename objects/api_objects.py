from __future__ import annotations

import math


class SkyBlockPlayer:
    def __init__(
            self, uuid: str, player_data: dict = None, profile_id: str = None, profile_name: str = None,
            select_profile_on: str = "last_save"
    ):
        self.uuid = uuid
        self.player_data = player_data
        if player_data.get("profiles"):
            for profile in player_data["profiles"]:
                if self.uuid not in profile["members"]:
                    self.player_data["profiles"].remove(profile)

        """
        select_profile_on can be one of the following:
        - last_save
        - weight
        - cata
        - slayer
        """
        self._name, self._weight_with_overflow, self._weight_without_overflow, self.profile, self.gexp, _selected_profile_name = (
                                                                                                                                     None,) * 6

        self.select_profile(profile_id, profile_name, select_profile_on)

        self._dungeons_level50_experience = 569809640
        self._skills_level50_experience = 55172425
        self._skills_level60_experience = 111672425
        self._dungeon_weights = {
            "catacombs": 0.0002149604615,
            "healer": 0.0000045254834,
            "mage": 0.0000045254834,
            "berserk": 0.0000045254834,
            "archer": 0.0000045254834,
            "tank": 0.0000045254834,
        }
        self._slayer_weights = {
            "zombie": {
                "divider": 2208,
                "modifier": 0.15,
            },
            "spider": {
                "divider": 2118,
                "modifier": 0.08,
            },
            "wolf": {
                "divider": 1962,
                "modifier": 0.015,
            },
            "enderman": {
                "divider": 1430,
                "modifier": 0.017,
            }
        }
        self._skill_weights = {
            # Maxes out mining at 1,750 points at 60.
            "mining": {
                "exponent": 1.18207448,
                "divider": 259634,
                "maxLevel": 60,
            },
            # Maxes out foraging at 850 points at level 50.
            "foraging": {
                "exponent": 1.232826,
                "divider": 259634,
                "maxLevel": 50,
            },
            # Maxes out enchanting at 450 points at level 60.
            "enchanting": {
                "exponent": 0.96976583,
                "divider": 882758,
                "maxLevel": 60,
            },
            # Maxes out farming at 2,200 points at level 60.
            "farming": {
                "exponent": 1.217848139,
                "divider": 220689,
                "maxLevel": 60,
            },
            # Maxes out combat at 1,500 points at level 60.
            "combat": {
                "exponent": 1.15797687265,
                "divider": 275862,
                "maxLevel": 60,
            },
            # Maxes out fishing at 2,500 points at level 50.
            "fishing": {
                "exponent": 1.406418,
                "divider": 88274,
                "maxLevel": 50,
            },
            # Maxes out alchemy at 200 points at level 50.
            "alchemy": {
                "exponent": 1.0,
                "divider": 1103448,
                "maxLevel": 50,
            },
            # Maxes out taming at 500 points at level 50.
            "taming": {
                "exponent": 1.14744,
                "divider": 441379,
                "maxLevel": 50,
            },
            # Sets up carpentry and runecrafting without any weight components.
            "carpentry": {
                "maxLevel": 50,
            },
            "runecrafting": {
                "maxLevel": 25,
            },
        }
        self._skill_weight_groups = [
            'mining', 'foraging', 'enchanting', 'farming', 'combat', 'fishing', 'alchemy', 'taming'
        ]

    def _selected_profile(
            self, profile_id: str = None, profile_name: str = None, select_profile_on: str = "last_save"
    ) -> dict:
        if self.player_data["profiles"] is None:
            self._selected_profile_name = None
            return None
        if profile_id:
            for profile in self.player_data["profiles"]:
                if profile["profile_id"] == profile_id:  # and self.uuid in profile["members"]:
                    self._selected_profile_name = profile["cute_name"]
                    return profile["members"][self.uuid]
        if profile_name:
            for profile in self.player_data["profiles"]:
                if profile["cute_name"] == profile_name:
                    self._selected_profile_name = profile["cute_name"]
                    return profile["members"][self.uuid]

        profiles = []
        for profile in self.player_data["profiles"]:
            try:
                profile["members"][self.uuid]["cute_name"] = profile["cute_name"]
                profiles.append(profile["members"][self.uuid])
            except KeyError:
                continue

        if select_profile_on == "last_save":
            found_profile = sorted(profiles, key=lambda x: x.get("last_save", 0), reverse=True)[0]

        elif select_profile_on == "weight":
            found_profile = sorted(
                self.player_data["profiles"],
                key=lambda x: SkyBlockPlayer(self.uuid, self.player_data, x["profile_id"]).weight(),
                reverse=True
            )[0]["members"][self.uuid]
        elif select_profile_on == "cata":
            found_profile = sorted(
                profiles,
                key=lambda x: x.get("dungeons", {}).get("dungeon_types", {}).get("catacombs", {}).get("experience", 0),
                reverse=True
            )[0]
        elif select_profile_on == "slayer":
            found_profile = sorted(
                profiles,
                key=lambda x: sum([i.get("xp", 0) for i in x.get("slayer_bosses", {}).values()]),
                reverse=True
            )[0]
        else:
            raise ValueError(f"Invalid select_profile_on: {select_profile_on}")

        self._selected_profile_name = found_profile["cute_name"]
        return found_profile

    def select_profile(self, profile_id: str = None, profile_name: str = None, select_profile_on: str = "last_save"):
        """
        select_profile_on can be one of the following:
        - last_save
        - weight
        - cata
        - slayer
        """

        self.profile = self._selected_profile(profile_id, profile_name, select_profile_on)
        self._weight_with_overflow, self._weight_without_overflow = None, None
        return self

    async def get_name(self, app) -> str:
        if self._name:
            return self._name
        self._name = await app.httpr.get_name(self.uuid)
        return self._name

    @staticmethod
    def get_cata_lvl(exp):
        levels = {
            '1': 50, '2': 125, '3': 235, '4': 395, '5': 625, '6': 955, '7': 1425, '8': 2095, '9': 3045,
            '10': 4385, '11': 6275, '12': 8940, '13': 12700, '14': 17960, '15': 25340, '16': 35640,
            '17': 50040, '18': 70040, '19': 97640, '20': 135640, '21': 188140, '22': 259640, '23': 356640,
            '24': 488640, '25': 668640, '26': 911640, '27': 1239640, '28': 1684640, '29': 2284640,
            '30': 3084640, '31': 4149640, '32': 5559640, '33': 7459640, '34': 9959640, '35': 13259640,
            '36': 17559640, '37': 23159640, '38': 30359640, '39': 39559640, '40': 51559640, '41': 66559640,
            '42': 85559640, '43': 109559640, '44': 139559640, '45': 177559640, '46': 225559640,
            '47': 285559640, '48': 360559640, '49': 453559640, '50': 569809640
        }
        for level in levels:
            if exp >= levels["50"]:
                return 50
            if levels[level] > exp:
                if int(level) == 1:
                    level = str(2)
                lowexp = levels[str(int(level) - 1)]
                highexp = levels[level]
                difference = highexp - lowexp
                extra = exp - lowexp
                percentage = (extra / difference)
                return (int(level) - 1) + percentage

    def get_skill_lvl(self, skill_type, exp):
        skill_weight = self._skill_weights[skill_type]
        levels = {
            "0": 0, "1": 50, "2": 175, "3": 375, "4": 675, "5": 1175, "6": 1925, "7": 2925, "8": 4425, "9": 6425,
            "10": 9925, "11": 14925, "12": 22425, "13": 32425, "14": 47425, "15": 67425, "16": 97425, "17": 147425,
            "18": 222425, "19": 322425, "20": 522425, "21": 822425, "22": 1222425, "23": 1722425, "24": 2322425,
            "25": 3022425, "26": 3822425, "27": 4722425, "28": 5722425, "29": 6822425, "30": 8022425, "31": 9322425,
            "32": 10722425, "33": 12222425, "34": 13822425, "35": 15522425, "36": 17322425, "37": 19222425,
            "38": 21222425, "39": 23322425, "40": 25522425, "41": 27822425, "42": 30222425, "43": 32722425,
            "44": 35322425, "45": 38072425, "46": 40972425, "47": 44072425, "48": 47472425, "49": 51172425,
            "50": 55172425, "51": 59472425, "52": 64072425, "53": 68972425, "54": 74172425, "55": 79672425,
            "56": 85472425, "57": 91572425, "58": 97972425, "59": 104672425, "60": 111672425
        }
        for level in levels:
            if exp >= levels[str(skill_weight["maxLevel"])]:
                return skill_weight["maxLevel"]
            if levels[level] > exp:
                lowexp = levels[str(int(level) - 1)]
                highexp = levels[level]
                difference = highexp - lowexp
                extra = exp - lowexp
                percentage = (extra / difference)
                return (int(level) - 1) + percentage

    @property
    def selected_profile_name(self):
        return self._selected_profile_name

    @property
    def last_save(self):
        try:
            return self.profile["last_save"]
        except (KeyError, TypeError):
            return None

    @property
    def catacombs_xp(self) -> float:
        try:
            return self.profile["dungeons"]["dungeon_types"]["catacombs"]["experience"]
        except (KeyError, TypeError):
            return 0

    @property
    def catacombs_level(self) -> float:
        return self.get_cata_lvl(self.catacombs_xp)

    def _calculate_dungeon_weight(self, weight_type: str, level: int, experience: int, with_overflow: bool = True):
        percentage_modifier = self._dungeon_weights[weight_type]

        # Calculates the base weight using the players level
        base = math.pow(level, 4.5) * percentage_modifier

        # If the dungeon XP is below the requirements for a level 50 dungeon we'll
        # just return our weight right away.
        if experience <= self._dungeons_level50_experience:
            return base

        # Calculates the XP above the level 50 requirement, and the splitter
        # value, weight given past level 50 is given at 1/4 the rate.
        remaining = experience - self._dungeons_level50_experience
        splitter = (4 * self._dungeons_level50_experience) / base

        # Calculates the dungeon overflow weight and returns it to the weight object builder.

        # return {
        #     "weight": math.floor(base),
        #     "weight_overflow": math.pow(remaining / splitter, 0.968),
        # }
        return math.floor(base) + math.pow(remaining / splitter, 0.968) if with_overflow else math.floor(base)

    def dungeon_weight(self, with_overflow: bool = True):
        if self.profile is None or self.profile.get("dungeons") is None:
            return 0
        return sum(
            self._calculate_dungeon_weight(
                cls_data, self.get_cata_lvl(exp.get("experience", 0)), exp.get("experience", 0), with_overflow
            ) for cls_data, exp in self.profile["dungeons"]["player_classes"].items()
        ) + self._calculate_dungeon_weight("catacombs", self.catacombs_level, self.catacombs_xp, with_overflow)

    @property
    def slayer_xp(self) -> float:
        if self.profile and self.profile.get("slayer_bosses") is not None:
            return sum([i.get("xp", 0) for i in self.profile.get("slayer_bosses", {}).values()])
        return 0

    def _calculate_slayer_weight(self, weight_type: str, experience: int, with_overflow: bool = True):
        slayer_weight = self._slayer_weights.get(weight_type)
        if not slayer_weight:
            return 0

        if experience <= 1000000:
            return 0 if experience <= 0 else experience / slayer_weight["divider"]

        base = 1000000 / slayer_weight["divider"]
        remaining = experience - 1000000

        modifier = slayer_weight["modifier"]
        overflow = 0

        while remaining > 0:
            left = min(remaining, 1000000)

            overflow += math.pow(left / (slayer_weight["divider"] * (1.5 + modifier)), 0.942)
            modifier += slayer_weight["modifier"]
            remaining -= left

        return base + overflow if with_overflow else base

    def slayer_weight(self, with_overflow: bool = True):
        if self.profile is None or self.profile.get("slayer_bosses") is None:
            return 0
        return sum(
            self._calculate_slayer_weight(
                slayer_type,
                self.profile["slayer_bosses"].get(slayer_type, {}).get("xp", 0) if self.profile else 0,
                with_overflow
            )
            for slayer_type in self._slayer_weights.keys()
        )

    def _calculate_skill_weight(self, weight_type: str, level: int, experience: int, with_overflow: bool = True):
        skill_weight = self._skill_weights.get(weight_type)
        if not skill_weight or skill_weight["divider"] == 0 or skill_weight["exponent"] == 0:
            return 0

        # Gets the XP required to max out the skill.
        max_skill_level_xp = self._skills_level60_experience if skill_weight["maxLevel"] == 60 \
            else self._skills_level50_experience

        # Calculates the base weight using the players level, if the players level
        # is 50/60 we'll round off their weight to get a nicer looking number.
        base = math.pow(level * 10, 0.5 + skill_weight["exponent"] + level / 100) / 1250
        if experience > max_skill_level_xp:
            base = round(base)

        # If the skill XP is below the requirements for a level 50/60 skill we'll
        # just return our weight to the weight object builder right away.
        if experience <= max_skill_level_xp:
            return base

        # Calculates the skill overflow weight and returns it to the weight object builder.
        return base + math.pow((experience - max_skill_level_xp) / skill_weight["divider"], 0.968) if with_overflow \
            else base

    def skill_weight(self, with_overflow: bool = True):
        if self.profile is None:
            return 0

        r = 0
        for skill_type in self._skill_weights.keys():
            if skill_type in self._skill_weight_groups:
                experience = self.profile.get(f"experience_skill_{skill_type}", 0)
                r += self._calculate_skill_weight(
                    skill_type, self.get_skill_lvl(skill_type, experience), experience, with_overflow
                )
        return r

    @property
    def average_skill(self):
        if self.profile is None:
            return 0
        r = 0
        for skill_type in self._skill_weight_groups:
            experience = self.profile.get(f"experience_skill_{skill_type}", 0)
            r += self.get_skill_lvl(skill_type, experience)
        return r / len(self._skill_weight_groups)

    def weight(self, with_overflow: bool = True):
        if with_overflow:
            if self._weight_with_overflow:
                return self._weight_with_overflow
            self._weight_with_overflow = self.slayer_weight(with_overflow) + self.skill_weight(
                with_overflow) + self.dungeon_weight(with_overflow)
            return self._weight_with_overflow
        else:
            if self._weight_without_overflow:
                return self._weight_without_overflow
            self._weight_without_overflow = self.slayer_weight(with_overflow) + self.skill_weight(
                with_overflow) + self.dungeon_weight(with_overflow)
            return self._weight_without_overflow