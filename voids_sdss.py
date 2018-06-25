'''VoidFinder - Hoyle & Vogeley (2002)'''


################################################################################
#
#   IMPORT MODULES
#
################################################################################


import numpy as np
from astropy.table import Table
#from scipy import spatial
from sklearn import neighbors

from voidfinder_functions import mesh_galaxies, in_mask, in_survey
from table_functions import add_row, subtract_row, to_vector, to_array

from avsepcalc import av_sep_calc
from mag_cutoff_function import mag_cut, field_gal_cut


################################################################################
#
#   USER INPUTS
#
################################################################################


# Input file names
in_filename = 'SDSSdr7/vollim_dr7_cbp_102709.dat' # File format: RA, dec, redshift, comoving distance, absolute magnitude
mask_filename = 'SDSSdr7/cbpdr7mask.dat' # File format: RA, dec

# Output file names
out1_filename = 'SDSSdr7/out1_vollim_dr7_cbp_102709.dat' # List of maximal spheres of each void region: x, y, z, radius, distance, ra, dec
out2_filename = 'SDSSdr7/out2_vollim_dr7_cbp_102709.dat' # List of holes for all void regions: x, y, z, radius, flag (to which void it belongs)
out3_filename = 'SDSSdr7/out3_vollim_dr7_cbp_102709.dat' # List of void region sizes: radius, effective radius, evolume, x, y, z, deltap, nfield, vol_maxhole
voidgals_filename = 'SDSSdr7/vollim_voidgals_dr7_cbp_102709.dat' # List of the void galaxies: x, y, z, void region #


################################################################################
#
#   INITIALIZATIONS
#
################################################################################
print('Initializations')

ngrid = 128       # Number of grid cells
maskra = 360
maskdec = 180
dec_offset = -90
max_dist = 300.    # z = 0.107 -> 313 h-1 Mpc   z = 0.087 -> 257 h-1 Mpc
min_dist = 0.

box = 630.        # Size of survey/simulation box
dl = box/ngrid    # length of each side of the box
voidmax = 100.
ioff2 = voidmax/dl + 2

dr = 1. # Distance to shift the hole centers

frac = 0.1

print('Number of grid cells is', ngrid, dl, box, ioff2)

# Constants
c = 3e5
DtoR = np.pi/180.
RtoD = 180./np.pi


################################################################################
#
#   OPEN FILES
#
################################################################################
print('Opening files')

infile = Table.read(in_filename, format='ascii.commented_header')

infile = mag_cut(infile,-20)

xin = infile['Rgal']*np.cos(infile['ra']*DtoR)*np.cos(infile['dec']*DtoR)
yin = infile['Rgal']*np.sin(infile['ra']*DtoR)*np.cos(infile['dec']*DtoR)
zin = infile['Rgal']*np.sin(infile['dec']*DtoR)
coord_in_table = Table([xin, yin, zin], names=['x','y','z'])
#coord_min_table = np.amin(coord_in_table)
#coord_max_table = np.amax(coord_in_table)

coord_min_x = [min(coord_in_table['x'])]
coord_min_y = [min(coord_in_table['y'])]
coord_min_z = [min(coord_in_table['z'])]

coord_max_x = [max(coord_in_table['x'])]
coord_max_y = [max(coord_in_table['y'])]
coord_max_z = [max(coord_in_table['z'])]

coord_min_table = Table([coord_min_x, coord_min_y, coord_min_z], names=['x','y','z'])
coord_max_table = Table([coord_max_x, coord_max_y, coord_max_z], names=['x','y','z'])

N_gal = len(infile)

print('x:', coord_min_x[0], coord_max_x[0])
print('y:', coord_min_y[0], coord_max_y[0])
print('z:', coord_min_z[0], coord_max_z[0])
print('There are', N_gal, 'galaxies in this simulation.')

# Convert coord_in, coord_min, coord_max tables to numpy arrays
coord_in = to_array(coord_in_table)
coord_min = to_vector(coord_min_table)
coord_max = to_vector(coord_max_table)

print('Reading mask')

maskfile = Table.read(mask_filename, format='ascii.commented_header')
mask = np.zeros((maskra, maskdec))
mask[maskfile['ra'].astype(int), maskfile['dec'].astype(int) - dec_offset] = 1
vol = len(maskfile)

'''
import matplotlib.pyplot as plt
import sys

plt.imshow(mask)
plt.colorbar()
plt.show()

sys.exit()
'''

print('Read mask')

################################################################################
#
#   PUT THE GALAXIES ON A CHAIN MESH
#
################################################################################


print('Making the grid')
mesh_indices, ngal, chainlist, linklist = mesh_galaxies(coord_in_table, coord_min_table, dl, ngrid)


print('Made the grid')

print('Checking the grid')
grid_good = True

for i in range(ngrid):
    for j in range(ngrid):
        for k in range(ngrid):
            count = 0
            igal = chainlist[i,j,k]
            while igal != -1:
                count += 1
                igal = linklist[igal]
            if count != ngal[i,j,k]:
                print(i,j,k, count, ngal[i,j,k])
                grid_good = False
if grid_good:
    print('Grid construction was successful.')


################################################################################
#
#   SEPARATION
#
################################################################################
# Michaela - Comment out as much or as little of this following block of code as 
# you need, and insert the call to your distance filtering function here.  If 
# you have any questions of how to incorporate your function into this script, 
# let me know!
print('Finding sep')

l, avsep, sd, dists3 = av_sep_calc(coord_in_table)

print('Average separation of n3rd gal is', avsep)
print('The standard deviation is', sd)
#print(dists3[:10])


# l = 5.81637  # s0 = 7.8, gamma = 1.2, void edge = -0.8
# l = 7.36181  # s0 = 3.5, gamma = 1.4
# or force l to have a fixed number by setting l = ****

print('Going to build wall with search value', l)

f_coord_table, w_coord_table = field_gal_cut(coord_in_table, dists3, l)

f_coord = to_array(f_coord_table)
w_coord = to_array(w_coord_table)
#print('w_coord shape',w_coord.shape)

nf =  len(f_coord_table)
nwall = len(w_coord_table)

'''boolean = minsep3 > l

# Voids
nf = sum(boolean)
f_coord_table = coord_in_table[boolean]
f_coord = to_array(f_coord_table)

# Walls
nwall = sum(np.logical_not(boolean))
w_coord_table = coord_in_table[np.logical_not(boolean)]
w_coord = to_array(w_coord_table)'''

print('Number of field gals:', nf,'Number of wall gals:', nwall)


################################################################################
#
#   SET UP CELL GRID DISTRIBUTION
#
################################################################################
print('Setting up grid')

wall_mesh_indices, ngal_wall, chainlist_wall, linklist_wall = mesh_galaxies(w_coord_table, coord_min_table, dl, ngrid)

#print(wall_mesh_indices[:5])
#print(np.sum(ngal_wall))

print('Grid set up')
################################################################################
#
#   BUILD NEAREST-NEIGHBOR TREE
#
################################################################################


galaxy_tree = neighbors.KDTree(w_coord)


################################################################################
#
#   GROW HOLES
#
################################################################################
print('Growing holes')

# Center of the current cell
hole_center_table = Table(np.zeros(6), names=['x', 'y', 'z', 'r', 'ra', 'dec'])

# Initialize list of hole details
myvoids_x = []
myvoids_y = []
myvoids_z = []
myvoids_r = []

# Number of holes found
n_holes = 0

# Find where all the empty cells are
empty_indices = np.where(ngal_wall == 0)

#print(len(empty_indices[0]))

# Go through each empty cell in the grid
for empty_cell in range(len(empty_indices[0])):
    # Retrieve empty cell indices
    i = empty_indices[0][empty_cell]
    j = empty_indices[1][empty_cell]
    k = empty_indices[2][empty_cell]

    #print('Looking in empty cell', empty_cell, 'of', len(empty_indices[0]))

    # Calculate center coordinates of cell
    hole_center_table['x'] = (i + 0.5)*dl + coord_min_table['x']
    hole_center_table['y'] = (j + 0.5)*dl + coord_min_table['y']
    hole_center_table['z'] = (k + 0.5)*dl + coord_min_table['z']

    hole_center = to_vector(hole_center_table)

    # Check to make sure that the hole center is within the survey
    if not in_mask(hole_center_table, mask, [min_dist, max_dist]):
        continue

    index_offset = 0
    nposs = 0 # Just a loop-ending variable - value does not matter anywhere else in the code!

    # Find closest galaxy to cell center
    modv1, k1g = galaxy_tree.query(hole_center.T, k=1)

    modv1 = modv1[0]
    k1g = k1g[0]

    # Unit vector pointing from closest galaxy to cell center
    v1_unit = (hole_center.T - w_coord[k1g])/modv1
    #print(v1_unit.shape)
    #print(w_coord[k1g].shape)
    #print(k1g.shape)
    #print(modv1.shape)
    ############################################################################
    # We are going to shift the center of the hole by dr along the direction of 
    # the vector pointing from the nearest galaxy to the center of the empty 
    # cell.  From there, we will search within a radius of length the distance  
    # between the center of the hole and the first galaxy from the center of 
    # the hole to find the next nearest neighbors.  From there, we will 
    # minimize top/bottom to find which one is the next nearest galaxy that 
    # bounds the hole.
    ############################################################################

    galaxy_search = True

    while galaxy_search:

        # Shift hole center along unit vector
        hole_center = hole_center + dr*v1_unit.T
        #print(hole_center.shape)
        # Distance between hole center and nearest galaxy
        modv1 += dr

        # Search for nearest neighbors within modv1 of the hole center
        i_nearest, dist_nearest = galaxy_tree.query_radius(hole_center.T, r=modv1, return_distance=True)

        if len(i_nearest) > 1:
            # Found at least one other nearest neighbor!
            galaxy_search = False

            # Remove nearest galaxy from list
            boolean_nearest = i_nearest != k1g
            dist_nearest = dist_nearest[boolean_nearest]
            i_nearest = i_nearest[boolean_nearest]

            # Calculate vector pointing from nearest galaxy to next nearest galaxies
            BA = w_coord[k1g] - w_coord[i_nearest]

            bot = 2*np.dot(BA, v1_unit)
            top = np.sum(BA**2, axis=1)

            x2 = top/bot

            # Find index of 2nd nearest galaxy
            k2g_x2 = np.argmin(x2)
            k2g = i_nearest[k2g_x2]

            minx2 = x2[k2g_x2]
        elif not in_mask(hole_center_table, mask, [min_dist, max_dist]):
            # Hole is no longer within survey limits
            galaxy_search = False

    # print 'Found 2nd galaxy'

    # Check to make sure that the hole center is still within the survey
    if not in_mask(hole_center_table, mask, [min_dist, max_dist]):
        print('Hole center moved outside of mask.')
        continue

    # Calculate new hole center
    hole_radius = 0.5*sum(BA[k2g_x2]**2)/np.dot(BA[k2g_x2], v1_unit)
    hole_center = hole_radius*v1_unit

    # Check to make sure that the hole center is still within the survey
    if not in_mask(hole_center_table, mask, [min_dist, max_dist]):
        print('Hole center moved outside of mask.')
        continue

    ############################################################################
    # Now find the third nearest galaxy.
    ############################################################################

    # Find the midpoint between the two nearest galaxies
    midpoint = 0.5*(w_coord[k1g] + w_coord[k2g])                

    # Define the unit vector along which to move the hole center
    modv2 = np.linalg.norm(hole_center - midpoint)
    v2_unit = (hole_center - midpoint)/modv2

    # Same methodology as for finding the second galaxy

    galaxy_search = True

    while galaxy_search:

        # Shift hole center along unit vector
        hole_center = hole_center + dr*v2_unit

        # Calculate vector pointing from the hole center to the nearest galaxies
        Acenter = hole_center - w_coord[k1g]

        # Search for nearest neighbors within modv1 of the hole center
        i_nearest, dist_nearest = galaxy_tree.query_radius(hole_center.T, r=np.linalg.norm(Acenter), return_distance=True)

        if len(i_nearest) > 1:
            # Found at least one other nearest neighbor!
            galaxy_search = False

            # Remove two nearest galaxies from list
            boolean_nearest = np.logical_and(i_nearest != k1g, i_nearest != k2g)
            dist_nearest = dist_nearest[boolean_nearest]
            i_nearest = i_nearest[boolean_nearest]

            # Calculate vector pointing from next nearest galaxies to hole center
            Ccenter = w_coord[i_nearest] - hole_center

            bot = 2*np.dot((Ccenter - Acenter), v2_unit)
            top = dist_nearest**2 - sum(Acenter**2)

            x3 = top/bot

            # Find index of 3rd nearest galaxy
            k3g_x3 = np.argmin(x3)
            k3g = i_nearest[k3g_x3]

            minx3 = x3[k3g_x3]
        elif not in_mask(hole_center_table, mask, [min_dist, max_dist]):
            # Hole is no longer within survey limits
            galaxy_search = False

    # print 'Found 3rd galaxy'

    # Check to make sure that the hole center is still within the survey
    if not in_mask(hole_center_table, mask, [min_dist, max_dist]):
        print('Hole center moved outside of mask.')
        continue

    # Calculate new hole center
    hole_center = hole_center + minx3*v2_unit

    # Check to make sure that the hole center is still within the survey
    if not in_mask(hole_center_table, mask, [min_dist, max_dist]):
        print('Hole center moved outside of mask.')
        continue

    ############################################################################
    # Now find the 4th nearest neighbor
    #
    # Process is very similar as before, except we do not know if we have to 
    # move above or below the plane.  Therefore, we will find the next closest 
    # if we move above the plane, and the next closest if we move below the 
    # plane.
    ############################################################################

    # The vector along which to move the hole center is defined by the cross 
    # product of the vectors pointing between the three nearest galaxies.
    AB = w_coord[k1g] - w_coord[k2g]
    BC = w_coord[k2g] - w_coord[k3g]
    v3 = np.cross(AB,BC)
    modv3 = np.linalg.norm(v3)
    v3_unit = v3/modv3

    # First move in the direction of the unit vector defined above
    galaxy_search = True

    while galaxy_search:

        # Shift hole center along unit vector
        hole_center_41 = hole_center + dr*v3_unit

        # Calculate vector pointing from the hole center to the nearest galaxy
        Acenter = hole_center_41 - w_coord[k1g]

        # Search for nearest neighbors within R of the hole center
        i_nearest, dist_nearest = galaxy_tree.query_radius(hole_center_41.T, r=np.linalg.norm(Acenter),return_distance=True)

        if len(i_nearest) > 1:
            # Found at least one other nearest neighbor!
            galaxy_search = False

            # Remove two nearest galaxies from list
            boolean_nearest = np.logical_and.reduce((i_nearest != k1g, i_nearest != k2g, i_nearest != k3g))
            dist_nearest = dist_nearest[boolean_nearest]
            i_nearest = i_nearest[boolean_nearest]

            # Calculate vector pointing from hole center to next nearest galaxies
            Ccenter = w_coord[i_nearest] - hole_center_41

            bot = 2*np.dot((Ccenter - Acenter), v3_unit)
            top = dist_nearest**2 - sum(Acenter**2)

            x41 = top/bot

            # Find index of 3rd nearest galaxy
            k4g1_x41 = np.argmin(x41)
            k4g1 = i_nearest[k4g1_x41]

            minx41 = x41[k4g1_x41]
        elif not in_mask(hole_center_table, mask, [min_dist, max_dist]):
            # Hole is no longer within survey limits
            galaxy_search = False

    # print 'Found first potential 4th galaxy'

    # Calculate potential new hole center
    hole_center_41 = hole_center + minx41*v3_unit

    # Repeat same search, but shift the hole center in the other direction this time
    v3_unit = -v3_unit

    # First move in the direction of the unit vector defined above
    galaxy_search = True

    while galaxy_search:

        # Shift hole center along unit vector
        hole_center_42 = hole_center + dr*v3_unit

        # Calculate vector pointing from the hole center to the nearest galaxy
        Acenter = hole_center_42 - w_coord[k1g]

        # Search for nearest neighbors within R of the hole center
        i_nearest, dist_nearest = galaxy_tree.query_radius(hole_center_42.T, r=np.linalg.norm(Acenter),return_distance=True)

        if len(i_nearest) > 1:
            # Found at least one other nearest neighbor!
            galaxy_search = False

            # Remove two nearest galaxies from list
            boolean_nearest = np.logical_and.reduce((i_nearest != k1g, i_nearest != k2g, i_nearest != k3g))
            dist_nearest = dist_nearest[boolean_nearest]
            i_nearest = i_nearest[boolean_nearest]

            # Calculate vector pointing from hole center to next nearest galaxies
            Ccenter = w_coord[i_nearest] - hole_center_42

            bot = 2*np.dot((Ccenter - Acenter), v3_unit)
            top = dist_nearest**2 - sum(Acenter**2)

            x42 = top/bot

            # Find index of 3rd nearest galaxy
            k4g2_x42 = np.argmin(x42)
            k4g2 = i_nearest[k4g2_x42]

            minx42 = x42[k4g2_x42]
        elif not in_mask(hole_center_table, mask, [min_dist, max_dist]):
            # Hole is no longer within survey limits
            galaxy_search = False

    # print 'Found second potential 4th galaxy'

    # Calculate potential new hole center
    hole_center_42 = hole_center + minx42*v3_unit

    # Determine which is the 4th nearest galaxy
    if minx41 <= minx42 and in_mask(hole_center_41, mask, [min_dist, max_dist]):
        # The first 4th galaxy found is the next closest
        hole_center = hole_center_41
        k4g = k4g1
    elif minx42 < minx41 and in_mask(hole_center_42, mask, [min_dist, max_dist]):
        # The second 4th galaxy found is the next closest
        hole_center = hole_center_42
        k4g = k4g2
    else:
        # Neither hole center is within the mask - not a valid hole
        continue

    # Radius of the hole
    hole_radius = np.linalg.norm(hole_center - w_coord[k1g])

    # Save hole
    myvoids_x.append(hole_center[0])
    myvoids_y.append(hole_center[1])
    myvoids_z.append(hole_center[2])
    myvoids_r.append(hole_radius)

    n_holes += 1

print('Found a total of', n_holes, 'potential voids.')

################################################################################
#
#   SORT HOLES BY SIZE
#
################################################################################
print('Sorting holes by size')

myvoids_table = Table([myvoids_x, myvoids_y, myvoids_z, myvoids_r], names=['x','y','z','radius'])

# Remove all holes with radii smaller than 10 Mpc/h
boolean = myvoids_table['radius'] > 10.
myvoids_table = myvoids_table[boolean]

# Need to sort the potential voids into size order
myvoids_table.sort('radius')

print('Holes are sorted.')
################################################################################
#
#   FILTER AND SORT HOLES INTO UNIQUE VOIDS
#
################################################################################
# The largest hole is a void
print('Combining holes into unique voids')

# Initialize column to store unique void identifier
myvoids_table['flag'] = 0

# Unique void count
void_count = 0

# Initialize
v_index = [] # Index of v's in myvoids_table


for i in range(len(myvoids_table)):

    # Reset overlap flag
    overlap_flag = False

    # Set hole's flag to be current unique void count (assumes that it is its own void)
    myvoids_table['flag'] = void_count

    # Check to see if current hole overlaps by more than 50% volume with any previously identified voids
    for j in range(void_count):

        # Calculate the distance between the hole centers
        dist_centers = np.linalg.norm(to_vector(subtract_row(myvoids_table['x','y','z'][i], myvoids_table['x','y','z'][v_index[j]])))

        # Sum of hole radii
        radii_sum = myvoids_table['radius'][i] + myvoids_table['radius'][v_index[j]]

        '''Calculate the overlapping volume.  If greater than half the 
        volume of the smaller sphere, then accept it.  Otherwise don't.'''

        if dist_centers < 1:  # Why are we comparing the center separation to 1?
            overlap_flag = True
            myvoids_table['flag'][i] = j

        elif dist_centers <= radii_sum:
            volume = np.pi/(12*dist_centers)*(radii_sum - dist_centers)**2*(dist_centers**2 + 2*dist_centers*myvoids_table['radius'][v_index[j]] - 3*myvoids_table['radius'][v_index[j]]**2 + 2*dist_centers*myvoids_table['radius'][i] + 6*myvoids_table['radius'][v_index[j]]*myvoids_table['radius'][i] - 3*myvoids_table['radius'][i]**2)
            sphere_volume = 4*np.pi*myvoids_table['radius'][i]**3/3

            if volume > frac*sphere_volume:
                # These two spheres overlap by more than X%, so hole is not unique
                overlap_flag = True
                myvoids_table['flag'][i] = j

    if not overlap_flag:
        v_index.append(i)
        void_count += 1

print('Number of unique voids is', void_count)

# Save list of all void holes
myvoids_table.write(out2_filename, format='ascii.commented_header')


################################################################################
#
#   COMPUTE VOLUME OF EACH VOID
#
################################################################################
print('Compute void volumes')

# Initialize void volume array
void_vol = np.zeros(void_count)

nran = 10000

for i in range(void_count):
    nsph = 0
    rad = 4*myvoids_table['radius'][v_index[i]]

    for j in range(nran):
        rand_pos = add_row(np.random.rand(3)*rad, myvoids_table['x','y','z'][v_index[i]]) - 0.5*rad
        
        for k in range(len(myvoids_table)):
            if myvoids_table['flag'][k]:
                # Calculate difference between particle and sphere
                sep = sum(to_vector(subtract_row(rand_pos, myvoids_table['x','y','z'][k])))
                
                if sep < myvoids_table['radius'][k]**2:
                    # This particle lies in at least one sphere
                    nsph += 1
                    break
    
    void_vol[i] = (rad**3)*nsph/nran


################################################################################
#
#   IDENTIFY VOID GALAXIES
#
################################################################################
print('Assign field galaxies to voids')

# Count the number of galaxies in each void
nfield = np.zeros(void_count)

# Add void field to f_coord
f_coord['vID'] = -99

for i in range(nf): # Go through each void galaxy
    for j in range(len(myvoids_table)): # Go through each void
        if np.linalg.norm(to_vector(subtract_row(f_coord[i], myvoids_table['x','y','z'][j]))) < myvoids_table['radius'][j]:
            # Galaxy lives in the void
            nfield[myvoids_table['flag'][j]] += 1

            # Set void ID in f_coord to match void ID
            f_coord['vID'][i] = myvoids_table['flag'][j]

            break

f_coord.write(voidgals_filename, format='ascii.commented_header')


################################################################################
#
#   MAXIMAL HOLE FOR EACH VOID
#
################################################################################


# Initialize
maximal_spheres = Table()

maximal_spheres['x'] = myvoids_table['x'][v_index]
maximal_spheres['y'] = myvoids_table['y'][v_index]
maximal_spheres['z'] = myvoids_table['z'][v_index]
maximal_spheres['radius'] = myvoids_table['radius'][v_index]
maximal_spheres['r'] = np.linalg.norm([myvoids_table['x'][v_index],myvoids_table['y'][v_index],myvoids_table['z'][v_index]], axis=0)
maximal_spheres['ra'] = np.arctan(myvoids_table['y'][v_index]/myvoids_table['x'][v_index])*RtoD
maximal_spheres['dec'] = np.arcsin(myvoids_table['z'][v_index]/maximal_spheres['r'])*RtoD

# Adjust ra value as necessary
boolean = np.logical_and(maximal_spheres['y'] != 0, maximal_spheres['x'] < 0)
maximal_spheres['ra'][boolean] += 180.

maximal_spheres.write(out1_filename, format='ascii.commented_header')


################################################################################
#
#   VOID REGION SIZES
#
################################################################################


# Initialize
void_regions = Table()

void_regions['radius'] = myvoids_table['radius'][v_index]
void_regions['effective_radius'] = (void_vol*0.75/np.pi)**(1./3.)
void_regions['volume'] = void_vol
void_regions['x'] = myvoids_table['x'][v_index]
void_regions['y'] = myvoids_table['y'][v_index]
void_regions['z'] = myvoids_table['z'][v_index]
void_regions['deltap'] = (nfield - N_gal*void_vol/vol)/(N_gal*void_vol/vol)
void_regions['n_gal'] = nfield
void_regions['vol_maxHole'] = (4./3.)*np.pi*myvoids_table['radius'][v_index]**3/void_vol

void_regions.write(out3_filename, format='ascii.commented_header')


