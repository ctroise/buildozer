import subprocess
import os
from shutil import copyfile

def code():
    def slurp(adir, sizedict, namedict, DEBUG=False):
        dirdict = {}
        #namedict = {}
        #sizedict = {}
        for root, dirs, files in os.walk(adir):
            aastartswithdot = []
            aahasnodot = []
            aabadending = []
            for filename in files:
                #fullpath = f"{adir}/{filename}"
                if filename[0] == '.':
                    aastartswithdot.append(filename)
                    continue
                if filename.find(".") == -1:
                    aahasnodot.append(filename)
                    continue
                stub, ending = filename.split('.')
                if ending.lower() in ["azw", "ini"]:
                    aabadending.append(filename)
                    continue
                if ending.lower() not in ["jpg", "jpeg", "png", "bmp"]:
                    continue
                if filename not in dirdict:
                    dirdict[filename] = 1
                else:
                    _joe = 12
                #
                if filename not in namedict:
                    namedict[filename] = []
                namedict[filename].append(adir)
                #
                fullpath = f"{adir}/{filename}"
                filesize = os.path.getsize(fullpath)
                if filesize not in sizedict:
                    sizedict[filesize] = []
                sizedict[filesize].append(filename)
            if DEBUG:
                if aabadending or aahasnodot or aastartswithdot:
                    print()
                    print(f"DIR: {adir}:")
                    for xx in aabadending:
                        print(f"Bad ending, skipped: {xx}")
                    for xx in aahasnodot:
                        print(f"Has no dot, skipped: {xx}")
                    for xx in aastartswithdot:
                        print(f"Bad ending, skipped: {xx}")
                    print()
            break  # Don't walk the directory
            #
        #
        # for key, files in sizedict.items():
        #     if len(files) != 1:
        #         print("\n")
        #         for file in files:
        #             fullpath = f"{adir}/{file}"
        #             copyfile(fullpath, f"{adir}/DUPES_TO_CHECK/{file}")
        #             print(f"\t{file}")
        #         print("\n")
        #         _joe = 12
        return sizedict, namedict
    # -----------------------------------------------------------------------
    chip_itself = "E:"  # 942 photos
    photo_frame = "C:/Users/ctroi/OneDrive/Desktop/photo_frame_Jan_9_2023"                             # 1102
    mom =  "C:/Users/ctroi/OneDrive/Desktop/chip_for_mom_existing_stuff_Jan_2023"                      # 38  I got rid of these once I made mom's chip
    dupes = "C:/Users/ctroi/OneDrive/Desktop/chip_for_mom_existing_stuff_Jan_2023/DUPES_TO_CHECK"      # 


    size_dict = {}
    name_dict = {}
    #for dir in [photo_frame, mom]:
    for dir in [chip_itself]:
        size_dict, name_dict = slurp(dir, size_dict, name_dict)

    #C:\Users\ctroi\OneDrive\Desktop\chip_for_mom_existing_stuff_Jan_2023
    _joe = 12
    for filename, dirs in name_dict.items():
        if len(dirs) != 1:
            print("")
            print(f"\t{filename} is in both directories!")
            pf_fullpath = f"{photo_frame}/{filename}"
            pf_filesize = os.path.getsize(pf_fullpath)
            mom_fullpath = f"{mom}/{filename}"
            mom_filesize = os.path.getsize(mom_fullpath)
            #
            #program_name = "C:/Program Files (x86)/Notepad++/notepad++.exe"
            #program_name = "C:/Windows/system32/notepad.exe"
            #subprocess.Popen(["C:/Windows/system32/notepad.exe", fullpath1])
            #subprocess.Popen(["C:/Windows/system32/notepad.exe", fullpath2])
            #
            stub, end = filename.split(".")
            if pf_filesize == mom_filesize:
                copyfile(f"{photo_frame}/{filename}", f"{dupes}/Same_size/{stub}_pf.{end}")
                copyfile(f"{mom}/{filename}",         f"{dupes}/Same_size/{stub}_mom.{end}")
                os.rename(f"{mom}/{filename}",        f"{mom}/DELETE_{filename}")
            else:
                copyfile(f"{photo_frame}/{filename}", f"{dupes}/Different_size/{stub}_pf.{end}")
                #copyfile(f"{mom}/{filename}",         f"{dupes}/Different_size/{stub}_mom.{end}")
                os.rename(f"{mom}/{filename}",        f"{mom}/DELETE_{filename}")
            print("")
            _joe = 12

    if (2+2)/4 != 1:
        for key, files in size_dict.items():
            if len(files) != 1:
                print("\n")
                for file in files:
                    #fullpath = f"{adir}/{file}"
                    #copyfile(fullpath, f"{adir}/DUPES_TO_CHECK/{file}")
                    print(f"\t{file}")
                print("\n")
                _joe = 12

    return

if __name__ == '__main__':
    #code()
    pass
