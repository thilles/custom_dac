
import git
import os
import logging
import glob
import subprocess
import yaml

# Logger
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
LOGGER = logging.getLogger(__name__)

SECURITY_CONTENT_URL = "https://github.com/splunk/security_content"


class GithubService:

    def __init__(self, security_content_branch, PR_number = None):
        self.security_content_branch = security_content_branch
        self.security_content_repo_obj = self.clone_project(SECURITY_CONTENT_URL, f"security_content", f"develop")
        if PR_number:
            subprocess.call(["git", "-C", "security_content/", "fetch", "origin", "refs/pull/%d/head:%s"%(PR_number, security_content_branch)])

        self.security_content_repo_obj.git.checkout(security_content_branch)

    def clone_project(self, url, project, branch):
        LOGGER.info(f"Clone Security Content Project")
        repo_obj = git.Repo.clone_from(url, project, branch=branch)
        return repo_obj

    def get_changed_test_files(self):
        branch1 = self.security_content_branch
        branch2 = 'develop'
        g = git.Git('security_content')
        changed_test_files = []
        changed_detection_files = []
        if branch1 != 'develop':
            differ = g.diff('--name-status', branch2 + '...' + branch1)
            changed_files = differ.splitlines()

            for file_path in changed_files:
                # added or changed test files
                if file_path.startswith('A') or file_path.startswith('M'):
                    if 'tests' in file_path:
                        if not os.path.basename(file_path).startswith('ssa') and os.path.basename(file_path).endswith('.test.yml'):
                            if file_path not in changed_test_files:
                                changed_test_files.append(file_path)

                    # changed detections
                    if 'detections' in file_path:
                        if not os.path.basename(file_path).startswith('ssa') and os.path.basename(file_path).endswith('.yml'):
                            changed_detection_files.append(file_path)
                            #file_path_base = os.path.splitext(file_path)[0].replace('detections', 'tests') + '.test'
                            #file_path_new = file_path_base + '.yml'
                            #if file_path_new not in changed_test_files:
                            #    changed_test_files.append(file_path_new)

        #all files have the format A\tFILENAME or M\tFILENAME.  Get rid of those leading characters
        changed_test_files = [name.split('\t')[1] for name in changed_test_files if len(name.split('\t')) == 2]
        changed_detection_files = [name.split('\t')[1] for name in changed_detection_files if len(name.split('\t')) == 2]


        detections_to_test,_,_ = self.filter_test_types(changed_detection_files)
        for f in detections_to_test:
            file_path_base = os.path.splitext(f)[0].replace('detections', 'tests') + '.test'
            file_path_new = file_path_base + '.yml'
            if file_path_new not in changed_test_files:
                changed_test_files.append(file_path_new)

        
        
       
        
        print("Total things to test (test files and detection files changed): [%d]"%(len(changed_test_files)))
        #for l in changed_test_files:
        #    print(l)
        #print(len(changed_test_files))
        import time
        time.sleep(5)
        return changed_test_files

    def filter_test_types(self, test_files, test_types = ["Anomaly", "Hunting", "TTP"]):
        files_to_test = []
        files_not_to_test = []
        error_files = []
        for filename in test_files:
            try:
                with open(os.path.join("security_content", filename), "r") as fileData:
                    yaml_dict = list(yaml.safe_load_all(fileData))[0]
                    if 'type' not in yaml_dict.keys():
                        print("Failed to find 'type' in the yaml for: [%s]"%(filename))
                        error_files.append(filename)
                    if yaml_dict['type'] in test_types:
                        files_to_test.append(filename)
                    else:
                        files_not_to_test.append(filename)
            except Exception as e:
                print("Error on trying to scan [%s]: [%s]"%(filename, str(e)))
                error_files.append(filename)
        print("***Detection Information***\n"\
              "\tTotal Files       : %d"
              "\tFiles to test     : %d"
              "\tFiles not to test : %d"
              "\tError files       : %d"%(len(test_files), len(files_to_test), len(files_not_to_test), len(error_files)))
        import time
        time.sleep(5)
        return files_to_test, files_not_to_test, error_files    



                




