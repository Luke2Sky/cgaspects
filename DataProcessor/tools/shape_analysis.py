import numpy as np
from pathlib import Path
import trimesh
from scipy.spatial import ConvexHull
from sklearn.decomposition import PCA
from chmpy.shape.convex_hull import transform_hull
from chmpy.shape.reconstruct import reconstruct
from chmpy.shape.sht import SHT


class CrystalShape:

    def __init__(self, l_max=10):
        self.sht = SHT(l_max)

    def normalise_verts(self, verts):

        self.centered = verts - np.mean(verts, axis=0)
        norm = np.linalg.norm(self.centered, axis=1).max()
        self.centered /= norm

        return self.centered

    def read_XYZ(self, filepath):
        filepath = Path(filepath)

        if filepath.suffix == '.XYZ':
            self.xyz = np.loadtxt(filepath, skiprows=2)[:, 3:]
        if filepath.suffix == '.xyz':
            self.xyz = np.loadtxt(filepath, skiprows=2)
        
        return self.xyz

    def get_coeffs(self, filepath):

        xyz = self.read_XYZ(filepath)
        self.hull = ConvexHull(self.normalise_verts(xyz))
        self.coeffs = transform_hull(self.sht, self.hull)

        return self.coeffs

    def reference_shape(self, shapepath):
        if Path(shapepath).suffix == '.XYZ':
            self.coeffs = self.get_coeffs(shapepath)

        else:
            mesh = trimesh.load(shapepath)
            norm_verts = self.normalise_verts(mesh.vertices)
            self.stl_hull = ConvexHull(norm_verts)
            self.coeffs = transform_hull(self.sht, self.stl_hull)

        return self.coeffs

    def compare_shape(self, ref_coeffs, shape_coeffs):
        self.distance = np.linalg.norm(ref_coeffs - shape_coeffs)

        return self.distance

    def get_PCA(self, file, n=3):

        file = Path(file)
        filetype = file.suffix
        pca = PCA(n_components=n)

        if filetype is '.XYZ' or '.xyz':
            self.xyz = self.read_XYZ(filepath=file)
            pca.fit(self.normalise_verts(self.xyz))
        
        if filetype == '.stl':
            mesh = trimesh.load(file)
            norm_verts = self.normalise_verts(mesh.vertices)
            self.stl_hull = ConvexHull(norm_verts)
            self.coeffs = transform_hull(self.sht, self.stl_hull)
            self.points = list(reconstruct(coefficients=self.coeffs))
            pca.fit(self.points)

        # pca_vectors = pca.components_
        # pca_values = pca.explained_variance_ratio_
        pca_svalues = pca.singular_values_

        # print(pca_vectors)
        # print(pca_values)
        # print(pca_svalues)s

        return pca_svalues

    def get_PCA_all(self, file, n=3):
        points = self.read_XYZ(filepath=file)

        pca = PCA(n_components=n)
        pca.fit(self.normalise_verts(points))
        pca_vectors = pca.components_
        pca_values = pca.explained_variance_ratio_
        pca_svalues = pca.singular_values_

        # print(pca_vectors)
        # print(pca_values)
        # print(pca_svalues)

        return (pca_svalues, pca_values, pca_vectors, points)

    def coeff_to_xyz(self, coeffs, 
                    path='.',
                    index=0,
                    name='',
                    write_txt=False):
        
        self.points = list(reconstruct(coefficients=coeffs))

        if write_txt:
            n_points = len(self.points)
            filepath = Path(path) / f'xyz_{name}_{index}.txt'
            with open(filepath, 'w') as xyz_file:
                xyz_file.write(f'{n_points}\n{filepath}\n')
                for line in self.points:
                    xyz_file.write(f'{line[0]}  {line[1]}  {line[2]}\n')

        return self.points