from modules import *

run_full = False
remove_high_mrat = True
save_fig = False
group_sizes = True
make_group_hdf5 = False

#remove_small_hs = False

out_p = ('/run/media/ppxrh2/166AA4B87A2DD3B7/MergerTreeAHF/Infalling_Groups/'
        'original_back_tracking/data_out_10.5-mass_limit_0.3-rat_cut')
suff = '_257.txt'

p_lim = 20
m_rat = 0.3
mstarlim = 10.**9.5
mlim = 10.**10.5

clus_ids = ld_arr(G3X_data+'ds_infor_G3X_progen/DS_G3X_snap_128_center-'
        'cluster_progenitors.txt', dtype='int')[:, 1]-(128*mod+1)  

#crange = np.array(np.arange(1, 325), dtype='int')
crange = np.array(np.loadtxt(G3X_data+'G3X_300_selected_sample_257.txt'), 
        dtype='int')

redshifts = ld_arr(G3X_data+'G3X_300_redshifts.txt')


def bound(vrels, rrel, m, r200):
    """ Determine whether a halo is bound to its host """
    rrels = rrel
    rrels[rrels==0.] = 0.001
    ke = 0.5 * (1000.*vrels)**2.
    ge = ((1.3271244*10.**20.) * m) / (3.0857*10.**19.)
    vir = (ke - (ge / rrels)) < (ge / (-2.5*r200))
    v_cr = 0.001*(1.2*ge/r200)**0.5
    return vir, rrels/r200, vrels/v_cr


def bound_crit(x):
    """ y = v/vcrit, x = r/R200, find boundness condition """
    return ((5./(3.*x)) - (2./3.))**0.5


def find_group_members(c):
    """ Finds bound group members, snapshot of infall, and quantities 
    including r200, stellar mass fraction, etc. of host """
    c_id = clus_ids[c-1]
    loaddir = ('/run/media/ppxrh2/166AA4B87A2DD3B7/MergerTreeAHF/MergerTree'
            'AHF_General_Tree_Comp/NewMDCLUSTER_'
            '%04d/snap_128/CLUSTER_%04d_' % (c, c))
    z_list = redshifts[c-1]

    npar_i = ld_arr(loaddir+'npars.txt', dtype='int')[:,-1]
    npar_i = np.where(npar_i >= p_lim)[0][-1]
    ids_i = ld_arr(loaddir[:-1]+'.txt')[:npar_i+1]
    xs_i = ld_arr(loaddir+'xs.txt')[:npar_i+1]
    ys_i = ld_arr(loaddir+'ys.txt')[:npar_i+1]
    zs_i = ld_arr(loaddir+'zs.txt')[:npar_i+1]
    vx_i = ld_arr(loaddir+'vx.txt')[:npar_i+1]
    vy_i = ld_arr(loaddir+'vy.txt')[:npar_i+1]
    vz_i = ld_arr(loaddir+'vz.txt')[:npar_i+1]
    ms_i = ld_arr(loaddir+'ms.txt')[:npar_i+1]
    mstars = ld_arr(loaddir+'mstars.txt', dtype='int')[:npar_i+1]
    starlim = (mstars < mstarlim) * (ms_i < mlim)
    rvirs_i = ld_arr(loaddir+'rvirs.txt')[:npar_i+1]
    subs_i = ld_arr(loaddir+'subs.txt', dtype='int')[:npar_i+1]
    
    ids_i[starlim] = 0.
    xs_i[starlim], ys_i[starlim], zs_i[starlim] = 0., 0., 0.
    vx_i[starlim], vy_i[starlim], vz_i[starlim] = 0., 0., 0.
    ms_i[starlim], rvirs_i[starlim], subs_i[starlim] = 0., 0., 0.
    mstars[starlim] = 0.

    bool_t = xs_i[:, -1]>0
    ids_i = ids_i[bool_t]
    xs_i, ys_i, zs_i = xs_i[bool_t], ys_i[bool_t], zs_i[bool_t]
    vx_i, vy_i, vz_i = vx_i[bool_t], vy_i[bool_t], vz_i[bool_t]
    ms_i, rvirs_i, subs_i = ms_i[bool_t], rvirs_i[bool_t], subs_i[bool_t]
    mstars = mstars[bool_t]

    m_rats = mstars / (ms_i + 0.001*(ms_i==0.))
    if remove_high_mrat == True:
        bool_t = m_rats < m_rat
        ids_i = ids_i*bool_t
        xs_i, ys_i, zs_i = xs_i*bool_t, ys_i*bool_t, zs_i*bool_t
        vx_i, vy_i, vz_i = vx_i*bool_t, vy_i*bool_t, vz_i*bool_t
        ms_i, rvirs_i, subs_i = ms_i*bool_t, rvirs_i*bool_t, subs_i*bool_t
        mstars = mstars*bool_t

        bool_t = m_rats[:, -1] < m_rat
        ids_i = ids_i[bool_t]
        xs_i, ys_i, zs_i = xs_i[bool_t], ys_i[bool_t], zs_i[bool_t]
        vx_i, vy_i, vz_i = vx_i[bool_t], vy_i[bool_t], vz_i[bool_t]
        ms_i, rvirs_i, subs_i = ms_i[bool_t], rvirs_i[bool_t], subs_i[bool_t]
        mstars = mstars[bool_t]

    #ensure cluster halo is not lost
    c_id = np.where(np.array(ids_i[:,-1],dtype='int')-(128*mod+1==c_id))[0][0]
    
    diff = ((xs_i-xs_i[c_id])**2. + (ys_i-ys_i[c_id])**2.
            + (zs_i-zs_i[c_id])**2.)**0.5

    offset = len(z_list) - len(diff[0])
    
    rs_tot = np.zeros(0)
    vs_tot = np.zeros(0)
    n_memb = np.array(np.zeros(0), dtype='int')
    r_virs = np.zeros(0)
    hostid = np.zeros((1, 2))
    z_infa = np.zeros(0)
    ratios = np.zeros(0)
    for h_id in range(len(xs_i)):
        snap = np.where(diff[h_id]<rvirs_i[c_id])[0]
        if len(snap) > 0:
            snap = snap[0]
        
            xs = (xs_i[:,snap] - xs_i[h_id,snap])
            ys = (ys_i[:,snap] - ys_i[h_id,snap])
            zs = (zs_i[:,snap] - zs_i[h_id,snap])
            rs = (xs**2. + ys**2. + zs**2.)**0.5

            vx = (vx_i[:,snap] - vx_i[h_id,snap])
            vy = (vy_i[:,snap] - vy_i[h_id,snap])
            vz = (vz_i[:,snap] - vz_i[h_id,snap])
            vs = (vx**2. + vy**2. + vz**2.)**0.5

            bs = list(bound(vs, rs, ms_i[h_id,snap], rvirs_i[h_id,snap]))
            bs[0][h_id]=False
            #remove bound objects more massive than host:
            bs[0] *= ms_i[:,snap] < ms_i[h_id,snap]

            rs_tot = np.append(rs_tot, bs[1][bs[0]])
            vs_tot = np.append(vs_tot, bs[2][bs[0]])
            n_memb = np.append(n_memb, int(np.sum(bs[0])))
            r_virs = np.append(r_virs, rvirs_i[h_id,snap])
            ratios = np.append(ratios, m_rats[h_id,snap])
            z_infa = np.append(z_infa, z_list[snap+offset])
            hostid = np.append(hostid, np.array([ids_i[h_id,[snap, -1]]]), 
                    axis=0)
    hostid = hostid[1:]
    
    print('group members: ' + str(np.sum(n_memb)))
    return rs_tot, vs_tot, n_memb, r_virs, z_infa, hostid, ratios


def find_group_num_dist(nm, lims):
    nm = nm[nm>0]
    total = float(len(nm))
    result = np.zeros(0)
    result = np.append(result, float(np.sum((nm <= lims[0]))) / total)
    for i in range(len(lims)-1):
        result = np.append(result, float(np.sum((nm > lims[i])*(nm <= 
                lims[i+1]))) / total)
    result = np.append(result, float(np.sum((nm > lims[-1]))) / total)
    return result


#######################################
#function needs revising and improving:
def find_group_paths(in_dir, suf):
    """ Writes final members of groups, and the snapshot of infall, 
    into a seperate HDF5 file for each cluster """
    groups = ld_arr(in_dir+'/groups'+suf, dtype='int')
    c_lis = groups[:, 0]
    ids = ld_arr(in_dir+'/host_ids'+suf, dtype='int')
    nms = np.transpose(ld_arr(in_dir+'/n_memb'+suf, dtype='int'))[0]

    ids = ids[nms>0] #ids of infalling hosts (~2000 hosts, with ~7000 sats)
    nms = nms[nms>0] #members in infalling hosts (sums to ~7000)
    nms_cu = np.zeros(len(nms))
    nms_cu[0] = nms[0]
    clus_cu = np.zeros(len(c_lis))
    clus_cu[0] = groups[0, 1]
    for i in range(len(nms)-1):
        nms_cu[i+1] = nms_cu[i]+nms[i+1]
    for i in range(len(groups)-1):
        clus_cu[i+1] = clus_cu[i]+groups[i+1, 1]
    nms_cu = np.array(nms_cu, dtype='int') 
    clus_cu = np.array(clus_cu, dtype='int')
    
    idlim_l = 0
    for c_i in range(len(c_lis)):
        c = c_lis[c_i]
        print(c)
        c_h = clus_ids[c-1]
        idlim_h = np.where(nms_cu == clus_cu[c_i])[0][0]+1
        grp_ids = ids[idlim_l:idlim_h]
        inf_snap = grp_ids[:, 0]/mod
        inf_id = grp_ids[:, 1] - (128*mod)
        idlim_l = idlim_h

        loaddir = ('/run/media/ppxrh2/166AA4B87A2DD3B7/MergerTreeAHF/Merger'
                'TreeAHF_General_Tree_Comp/NewMDCLUSTER_'
                '%04d/snap_128/CLUSTER_%04d_' % (c, c))
        npar_i = ld_arr(loaddir+'npars.txt', dtype='int')[:,-1]
        npar_i = np.where(npar_i < p_lim)[0][0]
        ids_i = ld_arr(loaddir[:-1]+'.txt', dtype='int')[:npar_i]
        xs_i = ld_arr(loaddir+'xs.txt')[:npar_i]
        ys_i = ld_arr(loaddir+'ys.txt')[:npar_i]
        zs_i = ld_arr(loaddir+'zs.txt')[:npar_i]
        vx_i = ld_arr(loaddir+'vx.txt')[:npar_i]
        vy_i = ld_arr(loaddir+'vy.txt')[:npar_i]
        vz_i = ld_arr(loaddir+'vz.txt')[:npar_i]
        ms_i = ld_arr(loaddir+'ms.txt')[:npar_i]
        starlim = ld_arr(loaddir+'mstars.txt', 
                dtype='int')[:npar_i] <= mstarlim
        rvirs_i = ld_arr(loaddir+'rvirs.txt')[:npar_i]
        subs_i = ld_arr(loaddir+'subs.txt', dtype='int')[:npar_i]
        mstars = ld_arr(loaddir+'mstars.txt', dtype='int')[:npar_i]
        
        ids_i[starlim] = 0.
        xs_i[starlim], ys_i[starlim], zs_i[starlim] = 0., 0., 0.
        vx_i[starlim], vy_i[starlim], vz_i[starlim] = 0., 0., 0.
        ms_i[starlim], rvirs_i[starlim], subs_i[starlim] = 0., 0., 0.

        bool_t = xs_i[:, -1]>0
        ids_i = ids_i[bool_t]
        xs_i, ys_i, zs_i = xs_i[bool_t], ys_i[bool_t], zs_i[bool_t]
        vx_i, vy_i, vz_i = vx_i[bool_t], vy_i[bool_t], vz_i[bool_t]
        ms_i, rvirs_i, subs_i = ms_i[bool_t], rvirs_i[bool_t], subs_i[bool_t]
        #####CHECKED TO HERE#####
        for i in range(len(inf_id)):
            inf_id[i] = np.sum(bool_t[:inf_id[i]])
        inf_snap = inf_snap - 129 + len(xs_i[0])
        inf_id = inf_id - 1

        hf = h5py.File('data_out_324/group_lists/cluster_%03d.hdf5' % c, 'w')
        
        for i in range(len(inf_snap)):
            xs = (xs_i[:,inf_snap[i]] - xs_i[inf_id[i],inf_snap[i]])
            ys = (ys_i[:,inf_snap[i]] - ys_i[inf_id[i],inf_snap[i]])
            zs = (zs_i[:,inf_snap[i]] - zs_i[inf_id[i],inf_snap[i]])
            rs = (xs**2. + ys**2. + zs**2.)**0.5

            vx = (vx_i[:,inf_snap[i]] - vx_i[inf_id[i],inf_snap[i]])
            vy = (vy_i[:,inf_snap[i]] - vy_i[inf_id[i],inf_snap[i]])
            vz = (vz_i[:,inf_snap[i]] - vz_i[inf_id[i],inf_snap[i]])
            vs = (vx**2. + vy**2. + vz**2.)**0.5

            bs = list(bound(vs, rs, ms_i[inf_id[i],inf_snap[i]], 
                    rvirs_i[inf_id[i],inf_snap[i]]))
            if remove_small_hs == True:
                bs[0][:inf_id[i]+1]=False
                bs[0] = bs[0] * (rvirs_i[inf_id[i],inf_snap[i]]>=6.5)
                bs[0][inf_id[i]]=True ###################
            else:
                bs[0][inf_id[i]]=False
            
            ids_t = ids_i[np.where(bs[0]==True)[0], -1]
            
            hf.create_dataset(str(ids_t[0]), data=np.append(ids_t[1:], 
                    inf_snap[i]+129-len(ids_i[0])))

    return None


if run_full == True:
    rs_total = np.zeros(0)
    vs_total = np.zeros(0)
    nm_total = np.zeros(0)
    r2_total = np.zeros(0)
    zi_total = np.zeros(0)
    mr_total = np.zeros(0)
    id_total = np.zeros((1, 2))
    member_no = np.zeros(0)
    total_no = np.zeros(0)

    for c_val in crange:
        print(c_val)
        result = find_group_members(c_val)
        rs_total = np.append(rs_total, result[0])
        vs_total = np.append(vs_total, result[1])
        nm_total = np.append(nm_total, result[2])
        r2_total = np.append(r2_total, result[3])
        zi_total = np.append(zi_total, result[4])
        id_total = np.append(id_total, result[5], axis=0)
        mr_total = np.append(mr_total, result[6])
        member_no = np.append(member_no, np.sum(result[2]))
        total_no = np.append(total_no, len(result[2]))
    id_total = id_total[1:]

    if not os.path.exists(out_p):
        os.mkdir(out_p)
    pd.DataFrame(np.char.mod('%12.9f', np.transpose(np.array(
            [rs_total, vs_total])))).to_csv(out_p+'/rs_vs'+suff, 
            sep='\t', index=None, header=[' r/R200_host', '    v/v_crit'])
    pd.DataFrame(np.char.mod('%6d', nm_total)).to_csv(out_p+'/n_memb'+suff,
            index=None, header=['n_memb'])
    pd.DataFrame(np.char.mod('%12.7f', r2_total)).to_csv(out_p+'/r_200s'+suff,
            index=None, header=['       r_200'])
    pd.DataFrame(np.char.mod('%10.8f', mr_total)).to_csv(out_p+'/ratios'+suff,
            index=None, header=['mstar/mtot'])
    pd.DataFrame(np.char.mod('%15d', id_total)).to_csv(out_p+'/host_ids'+suff,
            sep='\t', index=None, 
            header=['        host_id', '    z=0_host_id'])
    pd.DataFrame(np.char.mod('%6.3f', zi_total)).to_csv(out_p+'/z_infall'
            +suff, index=None, header=['z_infa'])
    pd.DataFrame(np.char.mod('%6d', np.transpose(np.array(
            [crange, member_no, total_no])))).to_csv(out_p+'/groups'+suff,
            sep='\t', index=None, header=['  c_id','groups','infall'])

else:
    rs_total, vs_total = np.transpose(ld_arr(out_p+'/rs_vs'+suff))
    zi_total = ld_arr(out_p+'/z_infall'+suff)
    nm_total = ld_arr(out_p+'/n_memb'+suff)
    r2_total = ld_arr(out_p+'/r_200s'+suff)
    mr_total = ld_arr(out_p+'/ratios'+suff)
    id_total = ld_arr(out_p+'/host_ids'+suff)
groups = ld_arr(out_p+'/groups'+suff)

mr_colour = np.zeros(0)
for i in range(len(nm_total)):
    mr_colour = np.append(mr_colour, np.array(int(nm_total[i])*list(mr_total[i])))

plt.figure()
plt.scatter(rs_total*1., vs_total, s=2., c='b')#mr_colour
#plt.colorbar()
print(len(rs_total))
plt.plot(np.arange(1, 251)/100., bound_crit(np.arange(1, 251)/100.), c='r', 
        linewidth=2.)
plt.xlim(0., 3.)
plt.ylim(0., 2.5)
plt.xlabel(r'$r/R_{\rm{200,group}}$')
plt.ylabel(r'$v/v_{\rm{crit}}$')
plt.tight_layout()
if save_fig==True:
    plt.savefig(out_p+'/fig1_masslim_rlim.pdf')
    plt.savefig(out_p+'/fig1_masslim_rlim.png', dpi=500)
plt.show()

def density_estimation(m1, m2, crop=False):
    """ Smoothed density for contour plot """
    x, y = np.linspace(xmin, xmax, steps), np.linspace(ymin, ymax, steps)
    X, Y = np.meshgrid(x, y)
    positions = np.vstack([X.ravel(), Y.ravel()])
    values = np.vstack([m1, m2])

    kernel = stats.gaussian_kde(values) 
    Z = np.reshape(kernel(positions).T, X.shape)

    if crop==True:
        bnd = Y < bound_crit(X)
        Z[bnd==False] = 0.

    return X, Y, Z



xmin, xmax, ymin, ymax, steps = 0., 2.6, 0., 2.5, 100
plt.figure(figsize=(8, 6))
X, Y, Z = density_estimation(rs_total, vs_total, True)
plt.contour(X, Y, Z, colors='b', levels=[0.3,0.5,0.7,0.9], 
        linewidths=[1., 1.5, 2., 2.5])#2.)
plt.plot((np.arange(1,2501)/1000.),bound_crit(np.arange(1,2501)/1000.), 
        c='k', linewidth=2.)
plt.xlim([xmin, xmax])
plt.ylim([ymin, ymax])
plt.show()


if group_sizes==True:
    grp_bins = [1, 17]
    print('Upper limits on group size bins: ' + str(grp_bins))
    print(find_group_num_dist(np.array(np.transpose(nm_total), 
            dtype='int')[0], grp_bins))


if make_group_hdf5==True:
    find_group_paths(out_p, suff)