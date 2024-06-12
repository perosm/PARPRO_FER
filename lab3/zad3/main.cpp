#include <stdio.h>
#include <stdlib.h>
#include <math.h>


#pragma warning(disable : 4996)

void jacobistep(double *psinew, double *psi, int m, int n)
{
	int i, j;
  
	for(i=1;i<=m;i++) {
		for(j=1;j<=n;j++) {
		psinew[i*(m+2)+j]=0.25*(psi[(i-1)*(m+2)+j]+psi[(i+1)*(m+2)+j]+psi[i*(m+2)+j-1]+psi[i*(m+2)+j+1]);
		}
	}
}


double deltasq(double *newarr, double *oldarr, int m, int n)
{
	int i, j;

	double dsq=0.0;
	double tmp;

	for(i=1;i<=m;i++)
	{
		for(j=1;j<=n;j++)
	{
		tmp = newarr[i*(m+2)+j]-oldarr[i*(m+2)+j];
		dsq += tmp*tmp;
		}
	}

	return dsq;
}

//grid is parallelised in the x direction

void boundarypsi(double *psi, int m, int n, int b, int h, int w)
{

	int i,j;

	//BCs on bottom edge

	for (i=b+1;i<=b+w-1;i++)
	{
		psi[i*(m+2)+0] = (double)(i-b);
	}

	for (i=b+w;i<=m;i++)
	{
		psi[i*(m+2)+0] = (double)(w);
	}

	//BCS on RHS

	for (j=1; j <= h; j++)
	{
		psi[(m+1)*(m+2)+j] = (double) w;
	}

	for (j=h+1;j<=h+w-1; j++)
	{
		psi[(m+1)*(m+2)+j]=(double)(w-j+h);
	}
}

void **arraymalloc2d(int nx, int ny, size_t typesize)
{
	int i;
	void **array2d;

	size_t mallocsize;

	// total memory requirements including pointers

	mallocsize = nx*sizeof(void *) + nx*ny*typesize;

	array2d = (void **) malloc(mallocsize);

	// set first pointer to first element of data

	array2d[0] = (void *) (array2d + nx);

	for(i=1; i < nx; i++)
	{
		// set other pointers to point at subsequent rows

		array2d[i] = (void *) (((char *) array2d[i-1]) + ny*typesize);
	}

	return array2d;
}


// time in seconds
#ifdef _WIN32 
#include <windows.h>
double gettime(void)
{
	LARGE_INTEGER fr, t;
	QueryPerformanceFrequency(&fr);
	QueryPerformanceCounter(&t);
	double t_sec = (t.QuadPart) / (double)fr.QuadPart;
	return t_sec;
}
#else
#include <sys/time.h>
double gettime(void)
{
  struct timeval tp;
  gettimeofday (&tp, NULL);
  return tp.tv_sec + tp.tv_usec/(double)1.0e6;
}
#endif


int main(int argc, char **argv)
{
	int printfreq=1000; //output frequency
	double error, bnorm;
	double tolerance=0.0; //tolerance for convergence. <=0 means do not check

	//main arrays
	double *psi;
	//temporary versions of main arrays
	double *psitmp;

	//command line arguments
	int scalefactor, numiter;

	//simulation sizes
	int bbase=10;
	int hbase=15;
	int wbase=5;
	int mbase=32;
	int nbase=32;

	int irrotational = 1, checkerr = 0;

	int m,n,b,h,w;
	int iter;
	int i,j;

	double tstart, tstop, ttot, titer;

	//do we stop because of tolerance?
	if (tolerance > 0) {checkerr=1;}

	//check command line parameters and parse them

	if (argc <3|| argc >4) {
		printf("Usage: cfd <scale> <numiter>\n");
		return 0;
	}

	scalefactor=atoi(argv[1]);
	numiter=atoi(argv[2]);

	if(!checkerr) {
		printf("Scale Factor = %i, iterations = %i\n",scalefactor, numiter);
	}
	else {
		printf("Scale Factor = %i, iterations = %i, tolerance= %g\n",scalefactor,numiter,tolerance);
	}

	printf("Irrotational flow\n");

	//Calculate b, h & w and m & n
	b = bbase*scalefactor;
	h = hbase*scalefactor;
	w = wbase*scalefactor;
	m = mbase*scalefactor;
	n = nbase*scalefactor;

	printf("Running CFD on %d x %d grid in serial\n",m,n);

	//allocate arrays
	psi    = (double *) malloc((m+2)*(n+2)*sizeof(double));
	psitmp = (double *) malloc((m+2)*(n+2)*sizeof(double));

	//zero the psi array
	for (i=0;i<m+2;i++) {
		for(j=0;j<n+2;j++) {
			psi[i*(m+2)+j]=0.0;
		}
	}

	//set the psi boundary conditions
	boundarypsi(psi,m,n,b,h,w);

	//compute normalisation factor for error
	bnorm=0.0;

	for (i=0;i<m+2;i++) {
			for (j=0;j<n+2;j++) {
			bnorm += psi[i*(m+2)+j]*psi[i*(m+2)+j];
		}
	}
	bnorm=sqrt(bnorm);

	//begin iterative Jacobi loop
	printf("\nStarting main loop...\n\n");
	tstart=gettime();

	for(iter=1;iter<=numiter;iter++) {

		//calculate psi for next iteration
		jacobistep(psitmp,psi,m,n);
	
		//calculate current error if required
		if (checkerr || iter == numiter) {
			error = deltasq(psitmp,psi,m,n);

			error=sqrt(error);
			error=error/bnorm;
		}

		//quit early if we have reached required tolerance
		if (checkerr) {
			if (error < tolerance) {
				printf("Converged on iteration %d\n",iter);
				break;
			}
		}

		//copy back
		for(i=1;i<=m;i++) {
			for(j=1;j<=n;j++) {
				psi[i*(m+2)+j]=psitmp[i*(m+2)+j];
			}
		}

		//print loop information
		if(iter%printfreq == 0) {
			if (!checkerr) {
				printf("Completed iteration %d\n",iter);
			}
			else {
				printf("Completed iteration %d, error = %g\n",iter,error);
			}
		}
	}	// iter

	if (iter > numiter) iter=numiter;

	tstop=gettime();

	ttot=tstop-tstart;
	titer=ttot/(double)iter;

	//print out some stats
	printf("\n... finished\n");
	printf("After %d iterations, the error is %g\n",iter,error);
	printf("Time for %d iterations was %g seconds\n",iter,ttot);
	printf("Each iteration took %g seconds\n",titer);

	//output results
	//writedatafiles(psi,m,n, scalefactor);
	//writeplotfile(m,n,scalefactor);

	//free un-needed arrays
	free(psi);
	free(psitmp);
	printf("... finished\n");

	return 0;
}