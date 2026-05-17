/*
 *  CFD_export_field.c
 *
 *  ANSYS Fluent UDF — per-timestep export of the full cell-centred
 *  temperature field as a CSV. Designed to be appended to the existing
 *  `bouyant_jet_replay/user_src/CFD_user.c`, or compiled separately into
 *  its own libudf.
 *
 *  Status: STAGED — this code is the same pattern as the validated
 *  `CFD_write_temperature` macro in the upstream tutorial (which loops
 *  the cells and aggregates to a scalar). It has NOT yet been compiled
 *  or run against an actual Fluent case in this repository. Treat it
 *  as a starting point, not as production-ready.
 *
 *  Output schema (one file per timestep):
 *
 *    field_TXXXX.csv          XXXX = zero-padded step counter
 *    -----------------------
 *    t_s,x_m,y_m,z_m,T_K      <-- header
 *    3.020000e+01,-0.05,0.001,0.02,2.930000e+02
 *    3.020000e+01, ...
 *
 *  Parameters (compile-time #defines below):
 *
 *    EXPORT_STRIDE     write every Nth timestep (set to 5 to match the
 *                      ~1 s cadence of the existing JPG snapshots)
 *    EXPORT_DIR        relative path for the CSVs ("post/CFD_reference/field/")
 *    EXPORT_PREFIX     filename prefix ("field_T")
 *
 *  Author: Mochamad Bukhori Zainun (k12438440)
 *          Johannes Kepler University Linz
 *  License: GPL-3.0, matching the upstream rCFD tutorial.
 */

#include "udf.h"

#include <stdio.h>
#include <string.h>


#if RP_NODE

    /* --- Tuneable parameters ----------------------------------------- */

    #define EXPORT_STRIDE   5                              /* every 5th step ≈ 1 s */
    #define EXPORT_DIR      "post/CFD_reference/field"     /* must exist */
    #define EXPORT_PREFIX   "field_T"

    static int  Field_export_step = 0;

#endif


/*************************************************************************************/
DEFINE_EXECUTE_AT_END(CFD_export_field)
/*************************************************************************************/
{
    /*  Writes one CSV file per timestep containing every cell-centred
     *  (x, y, z, T) tuple. The file is written by node-0 after every
     *  compute node serializes its cells through PRF_GISUM1/PRF_GRSUM*.
     *
     *  WARNING — naïve serial version: this version writes from each
     *  node sequentially to the same file (open mode "a"). For small
     *  meshes (~85 k cells, 4 partitions) this is fine. For large meshes
     *  it should be rewritten to pre-aggregate per-node buffers and have
     *  node-0 write once.
     */

#if RP_NODE

    if(Field_export_step % EXPORT_STRIDE != 0){

        Field_export_step++;

        return;
    }

    int       i_cell;
    double    x[3];

    Domain    *d = Get_Domain(1);
    Thread    *t = NULL;

    FILE      *f_out = NULL;
    char      filename[256];

    sprintf(filename, "%s/%s%04d.csv", EXPORT_DIR, EXPORT_PREFIX,
            Field_export_step / EXPORT_STRIDE);

    /* Node-0 writes the header first; other nodes append. */
    if(myid == 0){

        f_out = fopen(filename, "w");

        if(f_out == NULL){

            Message0("\nERROR: CFD_export_field could not open %s",
                     filename);

            return;
        }

        fprintf(f_out, "t_s,x_m,y_m,z_m,T_K\n");

        fclose(f_out);
    }

    /* Ordered append: node 0 first, then 1, 2, ... */
    {
        int    n;

        for(n = 0; n < compute_node_count; n++){

            if(myid == n){

                f_out = fopen(filename, "a");

                if(f_out != NULL){

                    thread_loop_c(t, d){begin_c_loop_int(i_cell, t){

                        C_CENTROID(x, i_cell, t);

                        fprintf(f_out, "%e,%e,%e,%e,%e\n",
                                CURRENT_TIME,
                                x[0], x[1], x[2],
                                C_T(i_cell, t));

                    }end_c_loop_int(i_cell, t)}

                    fclose(f_out);
                }
            }

            /* Synchronise so node n+1 only opens after node n closes. */
            PRF_GSYNC();
        }
    }

    if(myid == 0){

        Message0("\nCFD_export_field wrote %s\n", filename);
    }

    Field_export_step++;

#endif
}
