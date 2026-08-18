import os
import shutil

base_dir = "/home/ubuntu/poly-pmna-pdf-files/sitttr"

# Ensure uniform directory structure for model-question-papers and syllabus across revisions
revisions = ["revision-2015", "revision-2021", "revision-2026"]
categories = ["model-question-papers", "syllabus"]

print("Starting poly-pmna-pdf-files sitttr directory audit and reorganization...")

total_files = 0
for rev in revisions:
    rev_path = os.path.join(base_dir, rev)
    if not os.path.exists(rev_path):
        continue
    for cat in categories:
        cat_path = os.path.join(rev_path, cat)
        if not os.path.exists(cat_path):
            os.makedirs(cat_path, exist_ok=True)
            continue
        
        # Check departments
        depts = os.listdir(cat_path)
        for dept in depts:
            dept_path = os.path.join(cat_path, dept)
            if not os.path.isdir(dept_path):
                continue
            
            # Ensure semester subdirectories exist (semester-1 to semester-6, semester-unspecified)
            sems = ["semester-1", "semester-2", "semester-3", "semester-4", "semester-5", "semester-6", "semester-unspecified"]
            for sem in sems:
                sem_path = os.path.join(dept_path, sem)
                os.makedirs(sem_path, exist_ok=True)
                
            # Move any loose files in dept_path into semester-unspecified or appropriate semester
            for item in os.listdir(dept_path):
                item_path = os.path.join(dept_path, item)
                if os.path.isfile(item_path) and item.endswith('.pdf'):
                    # Default loose files to semester-unspecified if not already in a semester folder
                    dest = os.path.join(dept_path, "semester-unspecified", item)
                    if not os.path.exists(dest):
                        shutil.move(item_path, dest)
                        total_files += 1

print(f"Reorganization check complete. Processed and organized files successfully.")
