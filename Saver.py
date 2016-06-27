from os import getcwd

class saves(object):
    
    def __init__(self,N_PHI,N_save):
        self.savecount = 0
        self.N_save = N_save
        self.N_PHI = N_PHI
        self.save_step = self.N_PHI/self.N_save
        self.cwd = getcwd()
        self.are_we_save = False
        self.folder = ''
    
    def save_frame(self):
        if (frameCount%self.save_step == 0) and (self.savecount < self.N_save) and self.are_we_save:
            if self.savecount == 0:
                yr = str(year())[2:]
                mnt = '0'+str(month()) if month() < 10 else str(month())
                dy = '0'+str(day()) if day() < 10 else str(day())
                hr = '0'+str(hour()) if hour() < 10 else str(hour())
                mn = '0'+str(minute()) if minute() < 10 else str(minute())
                sc = '0'+str(second()) if second() < 10 else str(second())
                self.folder = '\\' + yr + '-' + mnt + '-' + dy + '-' + hr + mn + sc + '\\'
                filename = '0settings.txt'
                
                ### For when saving settings files ###
                ### Remember to include os.makedirs in imports ###
                
                # dirpath = self.cwd + self.folder
                # os.makedirs(dirpath)
                
                # settingdic = {'N_obj':N_obj, 'N_item':N_item, 'fade':fade, 'radius':radius,
                #               'xmult':xmult, 'ymult':ymult, 'N_save':N_save, 'axrot':axrot,
                #               'cerot':cerot, 'amp':amp, 'xw':xw, 'yw':yw, 'N_PHI':N_PHI}
                # with open(dirpath+filename, 'a') as ff:
                #     settings = ''
                #     for i in settingdic:
                #         linea = i + '\t=\t' + str(settingdic[i]) + '\n'
                #         settings += linea
                #     ff.write(settings)
            ### save_part for saving part of screen ##
            # save_part = get(0,0,540,540)
            # save_part.save(self.folder+str(self.savecount).zfill(6)+'.png')
            ### saveframe for saving all the screen ###
            saveFrame(self.folder+str(self.savecount).zfill(6)+'.png')
            self.savecount += 1
            print 'Saved frame ' + str(self.savecount) + ' of ' + str(self.N_save) +\
                ' in folder ' + str(self.folder)
        
        if self.savecount >= self.N_save:
                self.savecount = 0
                self.are_we_save = not self.are_we_save


    def onClick(self):
        self.are_we_save = not self.are_we_save
        if not self.are_we_save: self.savecount = 0
