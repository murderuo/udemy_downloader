import json  #developer mode
from pathlib import Path
import requests
from clint.textui import progress


def session_start(token):
    session=requests.Session()
    header={
        "Cookie":f"access_token={token}"
    }
    return session,header

def my_courses(ssn,hdr):
    url="https://www.udemy.com/api-2.0/users/me/subscribed-courses?page_size=1000"
    response=ssn.get(url=url,headers=hdr)
    status=response
    json_data=response.json()
    return status,json_data

def print_course_list(data): # kurs listesi >>> isim ve id
    course_list=data["results"]
    print(f"you have {len(course_list)} course... / {len(course_list)} kursunuz mevcut...")
    i=1
    for course in course_list:
        course_title=course["title"]
        # course_id=course_id_getter(course) #developer mode
        # print(i,f">> {course_title}  {course_id}") #developer mode
        print(i,f">> {course_title}  ")
        i+=1

def course_info_getter(data,input):
    course_list=data["results"]
    # print(course_list) #developer mode
    course=course_list[input-1]
    course_id = course_id_getter(course)
    title=course['title']
    # print(title) #developer mode
    return title,course_id

def course_id_getter(item):
    # print(item)
    course_id=item['id']
    return course_id

def course_chapter_and_lessons_getter(ssn,hdr,id):
    url = f"https://www.udemy.com/api-2.0/courses/{id}/cached-subscriber-curriculum-items/?page_size=1400"
    response=ssn.get(url=url,headers=hdr)
    response_json=response.json()
    results=response_json["results"]
    # print(results) #developer mode
    return results

def file_saver_html(title,html_item,folder_name):
    content=f"""<!DOCTYPE html>
    <html lang="tr">
    <head>
       <title>{title}</title>
    </head>
    <body><div style="width:800px; margin:0 auto;">
        {html_item}
        </div>
    </body>
    </html>"""
    file_name="".join("" if c in "\/:*?\"<>|!" else c for c in  title )
    file_name+=".html"
    folder_and_file_name=Path(folder_name/file_name)
    if not folder_and_file_name.exists():
        with open(folder_and_file_name,'w') as f:
            f.write(content)
            f.close()
    else:
        print(folder_and_file_name," file exists / dosya mevcut")

def file_saver_video(ssn,title,url,folder_name):
    title = "".join("" if c in "\/:*?\"<>|!" else c for c in title)
    filename = Path(folder_name / title)
    resp=ssn.get(url,stream=True)
    if not filename.exists():
        print(filename)
        with open(filename, 'wb') as f:
            total_length = int(resp.headers.get('content-length'))
            for chunk in progress.bar(resp.iter_content(chunk_size=1024), expected_size=(total_length / 1024) + 1):
                if chunk:
                    f.write(chunk)
                    f.flush()
    else:
        print(filename, " file exists / dosya mevcut")

def save_supplementary_assets(ssn,title,url,folder_name):
    title = "".join("" if c in "\/:*?\"<>|!" else c for c in title)
    filename = Path(folder_name / title)
    resp = ssn.get(url)
    if not filename.exists():
        print(filename)
        with open(filename, 'wb') as f:
            f.write(resp.content)
            f.close()
    else:
        print(filename, " file exists / dosya mevcut")


def course_video_item_saver(course_id,ssn,hdr,course_items,main_folder_obj):
    subfolder_path=""
    i=1
    sub=1
    for item in course_items:
        if item['_class'].lower()=='chapter':
            subfolder_path=create_subfolder(main_folder_obj,item['title'],sub)
            sub+=1
            continue
        elif item['_class'].lower()=='lecture':
            if item['asset']['asset_type'].lower()=='article':
                url = f'''https://www.udemy.com/api-2.0/users/me/subscribed-courses/{str(course_id)}/lectures/{item['id']}?fields[lecture]=asset,supplementary_assets&fields[asset]=stream_urls,download_urls,captions,title,filename,data,body,media_sources,media_license_token'''
                response=ssn.get(url,headers=hdr)
                response_json=response.json()
                file_saver_html(item['title'],response_json['asset']['body'],subfolder_path)
                if len(response_json['supplementary_assets'])!=0:
                    for s in response_json['supplementary_assets']:
                        # print(s) #developer mode
                        if s['download_urls'] == None:
                            continue
                        else:
                            supp_file_name = s['filename']
                            supp_url = s['download_urls']['File'][0]['file']
                            save_supplementary_assets(ssn,supp_file_name,supp_url,subfolder_path)
                    else:
                        print('no supplementary file / ek dosya yok')
            elif item['asset']['asset_type'].lower()=='video':
                url = f'''https://www.udemy.com/api-2.0/users/me/subscribed-courses/{str(course_id)}/lectures/{item['id']}?fields[lecture]=asset,supplementary_assets&fields[asset]=stream_urls,download_urls,captions,title,filename,data,body,media_sources,media_license_token'''
                response = ssn.get(url, headers=hdr)
                response_json = response.json()
                video_url=response_json['asset']['media_sources'][0]['src']
                video_file_name=str(i).zfill(3)+'-'+item['title_cleaned']+'.mp4'
                file_saver_video(ssn,video_file_name,video_url,subfolder_path)
                if len(response_json['supplementary_assets'])!=0:
                    for s in response_json['supplementary_assets']:
                        if s['download_urls']==None:continue
                        else:
                            supp_file_name = s['filename']
                            supp_url = s['download_urls']['File'][0]['file']
                            save_supplementary_assets(ssn,supp_file_name,supp_url,subfolder_path)
                else:
                    print('no supplementary file / ek dosya yok')
                i+=1
        elif item['_class'].lower() == 'quiz':
            print('this is Quiz, passing...','Quiz bölümü. atlanıyor ...')
            continue
        else:
            print("i didnt see this class please contact me https://twitter.com/murderuo")
            print("Bu bölümle karşılaşmadım, lütfen benimle irtibata geçin: https://twitter.com/murderuo")
            continue


def main_folder_creator(title):
    title="".join("" if c in "\/:*?\"<>|!." else c for c in  title )
    folder_name=Path(f'{title}')
    Path.mkdir(folder_name,parents=True,exist_ok=True)
    return folder_name

def create_subfolder(folder_obj,subfolder_name,number):
    subfolder_name="".join("" if c in "\/:*?\"<>|!." else c for c in  subfolder_name )
    subfolder=Path(f'{str(number).zfill(3)}-{subfolder_name}')
    fully_subfolder=Path(folder_obj/subfolder)
    Path.mkdir(fully_subfolder,parents=True,exist_ok=True)
    return  fully_subfolder

#we didnt use this function
# def save_a_json_file(fn,resp):
#     file_name=fn
#     with open(file_name+".json","w") as f:
#         json.dump(resp,f,indent=2)
#     print(f"dosya {fn}.json adıyla kaydedildi")
############################
'''
https://${subDomain}.udemy.com/api-2.0/users/me/subscribed-courses/${courseid}/lectures/${v.id}?fields[lecture]=asset,supplementary_assets&fields[asset]=stream_urls,download_urls,captions,title,filename,data,body,media_sources,media_license_token
'''
'''
f'https://www.udemy.com/api-2.0/users/me/subscribed-courses/{id}/lectures/{lecturer_id}?fields[lecture]=asset,supplementary_assets&fields[asset]=stream_urls,download_urls,captions,title,filename,data,body,media_sources,media_license_token'
'''


if __name__ == '__main__':
    access_token=input("pls give token / lütfen access token değerini giriniz : ")
    # access_token="XXXXXXXXXX"
    session,header=session_start(access_token)
    status,my_course_list=my_courses(session,header)
    print_course_list(my_course_list)
    secim=int(input('select the course to download / indirilecek kursu seciniz: '))
    title,id=course_info_getter(my_course_list,secim)
    #secilen kursun id ve başlığını getiriyor
    main_folder=main_folder_creator(title) #main folderi oluşturuyoruz ,bunu daha sonra fonksiyona göndereceğiz
    # course_chapter_and_lessons_getter(session, header, str(id)) #developer mode
    ###  1 >> Create Business Applications with AppSheet id:1387804 #developer mode
    course_items=course_chapter_and_lessons_getter(session,header,str(id))
    course_video_item_saver(id,session,header,course_items,main_folder)