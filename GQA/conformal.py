
import epic.imgpatch_conformal as imgpatch_conformal
import os

def init(dirname : str, thresh_str : str):
    GLOBAL_THRESHOLD = float(thresh_str)
    # SPLIT = args.split
    # GLOBAL_THRESHOLD = 1
    # GLOBAL_THRESHOLD = 0.5
    # GLOBAL_THRESHOLD = 0.25
    # GLOBAL_THRESHOLD = 0.125
    # SPLIT = "val"
    # SPLIT = "test"


    # split_indices = val_indices if SPLIT == "val" else test_indices
    # split_indices = val_indices if SPLIT == "val" else test_indices
    # split_ids = tuple(all_problem_ids[i] for i in split_indices)

    def scale_down(reference_point):
        return reference_point * GLOBAL_THRESHOLD

    def scale_up(reference_point):
        return 1 - ((1 - reference_point) * GLOBAL_THRESHOLD)

    imgpatch_conformal.ABSTRACT_EXISTS_UPPER = scale_up(0.75)
    imgpatch_conformal.ABSTRACT_EXISTS_LOWER = scale_down(0.25)
    imgpatch_conformal.ABSTRACT_FIND_HIGH = scale_up(0.5)
    imgpatch_conformal.ABSTRACT_FIND_LOW = scale_down(0.1)
    imgpatch_conformal.ABSTRACT_SIMPLE_QUERY_THRESHOLD = scale_down(0.5)
    imgpatch_conformal.ABSTRACT_VERIFYPROP_UPPER = scale_up(0.75)
    imgpatch_conformal.ABSTRACT_VERIFYPROP_LOWER = scale_down(0.25)

    imgpatch_conformal.CACHE_DIR = f"{dirname}/conformal_cache"
    os.makedirs(imgpatch_conformal.CACHE_DIR, exist_ok=True)