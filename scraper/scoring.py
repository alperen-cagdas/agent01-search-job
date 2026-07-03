from .schema import Job


def score_job(job: Job, profile: dict) -> Job:
    haystack_title = job.title.lower()
    haystack_body = f"{job.title} {job.description_snippet}".lower()
    location = (job.location or "").lower()

    weights = profile["weights"]
    matched = []
    score = 0.0

    primary_kw = [k.lower() for k in profile["role_keywords"]["primary"]]
    secondary_kw = [k.lower() for k in profile["role_keywords"]["secondary"]]
    skill_kw = [k.lower() for k in profile["skill_keywords"]]
    location_kw = [k.lower() for k in profile["location_keywords"]["preferred"]]

    primary_hit_title = next((k for k in primary_kw if k in haystack_title), None)
    if primary_hit_title:
        score += weights["primary_role_title_match"]
        matched.append(primary_hit_title)
    else:
        primary_hit_body = next((k for k in primary_kw if k in haystack_body), None)
        if primary_hit_body:
            score += weights["primary_role_body_match"]
            matched.append(primary_hit_body)

    secondary_hit = next((k for k in secondary_kw if k in haystack_body), None)
    if secondary_hit:
        score += weights["secondary_role_match"]
        matched.append(secondary_hit)

    skill_hits = [k for k in skill_kw if k in haystack_body]
    if skill_hits:
        bonus = min(len(skill_hits) * weights["skill_keyword_match"], weights["max_skill_bonus"])
        score += bonus
        matched.extend(skill_hits)

    location_hit = next((k for k in location_kw if k in location or k in haystack_body), None)
    if location_hit:
        score += weights["location_match"]
        matched.append(location_hit)

    job.score = score
    job.matched_keywords = sorted(set(matched))
    return job


def score_and_filter(jobs: list[Job], profile: dict) -> list[Job]:
    threshold = profile["scoring"]["minimum_score_threshold"]
    max_total = profile["scoring"]["max_total_results"]

    scored = [score_job(j, profile) for j in jobs]
    passed = [j for j in scored if j.score >= threshold]
    passed.sort(key=lambda j: (j.score, j.posted_date or ""), reverse=True)
    return passed[:max_total]
